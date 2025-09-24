import os
import requests
from geopy.geocoders import Nominatim
from datetime import datetime
import configparser
from pgdb import PGDatabase

dirname = os.path.dirname(__file__)

config = configparser.ConfigParser()
config.read(os.path.join(dirname,'config.ini'))

DATABASE_CREDS = config['Database']

database = PGDatabase(
    host=DATABASE_CREDS['HOST'],
    database=DATABASE_CREDS['DATABASE'],
    user=DATABASE_CREDS['USER'],
    port=DATABASE_CREDS['PORT'],
    password=DATABASE_CREDS['PASSWORD']
    )

def generate_city_params(city):
  geolocator = Nominatim(user_agent='abcd')
  location = geolocator.geocode(city)
  params = {
    'latitude': location.latitude,
    'longitude': location.longitude,
    'address': city
    }
  city_params = requests.get('https://user-geo-data.wildberries.ru/get-geo-info', params=params)
  return city_params

cities = ['Санкт-Петербург', 'Москва']
query_lst = ['джинсы', 'джинсы женские']
max_page = 2
brand = 'JOYCITY'
arr = []

for city in cities:

  address_info = generate_city_params(city).json()['xinfo']
    
  for query in query_lst:

    pos = 0

    for page in range(1,max_page+1):

      res = requests.get(f'''
        https://search.wb.ru/exactmatch/ru/common/v18/search?
        ab_testid=new_benefit_sort&
        inheritFilters=false&
        lang=ru&
        page={page}&
        query={query}&
        resultset=catalog&
        sort=popular&
        suppressSpellcheck=false&
        uclusters=0&
        {address_info}
       '''.replace('\n', '').replace(' ', '').strip())
        #headers="User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36")

      if res.status_code == 200:

        data = res.json()
        products = data.get('products', [])

        for card in products:

          pos += 1

          if card['brand'] == brand:

            if card.get('log'):
              arr.append([
                      card['name'],
                      card['log']['cpm'],
                      card['log']['position'],
                      card['log']['promoPosition'],
                      card['log']['tp'],
                      query,
                      datetime.now(),
                      city
                    ])
            else:
              arr.append([
                      card['name'],
                      0,
                      pos,
                      -1,
                      '-',
                      query,
                      datetime.now(),
                      city
                    ])
      else:
        print(f"Ошибка запроса: статус {res.status_code}")
      
for row in arr:
          database.post(
                '''
                insert into positions values (%s,%s,%s,%s,%s,%s,%s,%s)
                ''', row
              )    