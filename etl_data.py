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

cities = ['Москва', 'Санкт-Петербург']
address_info = {}
for city in cities:
  address_info[city] = generate_city_params(city).json()['xinfo']

query_lst = ['кроссовки мужские', 'кроссовки женские']
max_page = 2
brand = 'TimeJump'

for city in cities:
    
  for query in query_lst:
    arr = []
    pos = 0

    for page in range(1,max_page+1):
      res = requests.get(f'''
       https://search.wb.ru/exactmatch/ru/common/v18/search?
       ab_testing=false&
       inheritFilters=false&
       lang=ru&
       page={page}&
       query={query}&
       resultset=catalog&
       sort=popular&
       suppressSpellcheck=false&
       {address_info[city]}
       '''.replace('\n', '').replace(' ', '').strip())
      
      if res.status_code == 200:
        response = res.json()['products']
        for card in response:
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