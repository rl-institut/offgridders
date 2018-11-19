# not working
# see: https://www.renewables.ninja/documentation/api/python-example

import requests
import pandas as pd

api_base = 'https://www.renewables.ninja/api/'

s = requests.session()

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
    'capacity': 1,
    'system_loss': 0,
    'tracking': 0,
    'tilt': 0,
    'azim': 180,
    'format': 'csv',
    'metadata': False,
    'raw': False
}

r = s.get(url, params=args)

# Parse JSON to get a pandas.DataFrame
df = pd.read_csv(r.text, orient='index')

##
# Wind example
##

#url = api_base + 'data/wind'

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
