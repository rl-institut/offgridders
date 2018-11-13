'''
https://www.renewables.ninja/documentation/api/python-example
NOT EDITED AT ALL
'''

#This is an API access example using token-based authentication with Python.

import requests
import pandas as pd

token = 'your_token_here'
api_base = 'https://www.renewables.ninja/api/'

s = requests.session()
# Send token header with each request
s.headers = {'Authorization': 'Token ' + token}


##
# PV example
##

url = api_base + 'data/pv'

args = {
    'lat': 34.125,
    'lon': 39.814,
    'date_from': '2014-01-01',
    'date_to': '2014-12-31',
    'dataset': 'merra2',
    'capacity': 1.0,
    'system_loss': 10,
    'tracking': 0,
    'tilt': 35,
    'azim': 180,
    'format': 'json',
    'metadata': False,
    'raw': False
}

r = s.get(url, params=args)

# Parse JSON to get a pandas.DataFrame
df = pd.read_json(r.text, orient='index')

#Getting wind data works analogously:

##
# Wind example
##

url = api_base + 'data/wind'

args = {
    'lat': 34.125,
    'lon': 39.814,
    'date_from': '2014-01-01',
    'date_to': '2014-12-31',
    'capacity': 1.0,
    'height': 100,
    'turbine': 'Vestas V80 2000',
    'format': 'json',
    'metadata': False,
    'raw': False
}

r = s.get(url, params=args)
df = pd.read_json(r.text, orient='index')

