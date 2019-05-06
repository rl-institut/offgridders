import pandas as pd
import requests
import time
import logging
import pprint as pp
import os
from oemof.tools import logger

logger.define_logging(screen_level=logging.INFO)

##########################
# Read project file      #
##########################
logging.info('Reading from excel sheet')
path = "/home/local/RL-INSTITUT/martha.hoffmann/Desktop/Nextcloud/Masterthesis/Nigeria_Data/Nigeria_EnergyData_Plateau.csv"
data_set_ids = pd.read_csv(path, sep=';')

locations = data_set_ids[['NESP_ID', 'Lat', 'Lon']]

path = "./demand_profiles_nigeria_plateau.csv"
demands = pd.read_csv(path, sep=',').drop(['Unnamed: 0'], axis=1)
logging.info('Get data from renewable ninjas:')

token = 'f8c619d5a5a227629019fa61c24ce7bcd3c70ab9'
api_base = 'https://www.renewables.ninja/api/'

s = requests.session()
s.headers = {'Authorization': 'Token ' + token}

url_solar = api_base + 'data/pv'

time_zone_offset = -1 # negative: Earlier than german time zone ie. GER 12:00, Local 11:00, positive: later than german time zone

args_general = {
    'date_from': '2014-1-1',
    'date_to': '2014-12-31'}

datetimerange_local = pd.date_range(start='2014-1-1 0:00',  end='2014-12-31 23:00', freq='H')
datetimerange_367 = pd.date_range(start='2013-12-31 0:00', end='2015-1-1 23:00', freq='H')

args_pv = {
    'dataset': 'merra2',
    'capacity': 1.0,
    'system_loss': 10,
    'tracking': 0,
    'tilt': 6,
    'azim': 180,
    'format': 'json',
    'metadata': False,
    'raw': False
}
args_pv.update(args_general.copy())

url_wind = api_base + 'data/wind'

args_wind = {
    'capacity': 1.0,
    'height': 30,
    'turbine': 'Vestas V80 2000',
    'format': 'json',
    'metadata': False,
    'raw': False
}
args_wind.update(args_general.copy())

for name in locations.index:
    if os.path.isfile('../inputs/timeseries/nesp_' + str(data_set_ids["NESP_ID"][name]) + '.csv'):
        logging.info ('Timeseries for location ' + str(data_set_ids["NESP_ID"][name]) + ' already created.')

    else:
        logging.info('Requesting data for location ' + str(data_set_ids["NESP_ID"][name]))
        args_location = {
            'lat': locations['Lat'][name],
            'lon': locations['Lon'][name]}

        ########### PV ##############
        args_pv.update(args_location.copy())
        r = s.get(url_solar, params=args_pv)
        if r.status_code == 429:
            logging.info('Too many requests per minute')
        solar_generation = pd.read_json(r.text, orient='index')
        solar_generation = solar_generation['output']

        ########### Wind ###########
        args_wind.update(args_location.copy())
        r = s.get(url_wind, params=args_wind)
        if r.status_code == 429:
            logging.info('Too many requests per minute')
        wind_generation = pd.read_json(r.text, orient='index')
        wind_generation = wind_generation['output']

        ############ Add days to timeseries, perform transformation from rj data (German time zone) to local time zone) ###########

        day_jan_base = pd.date_range(start='2014-1-1 0:00',  end='2014-1-1 23:00', freq='H')
        day_jan_copy_to = pd.date_range(start='2015-1-1 0:00',  end='2015-1-1 23:00', freq='H')

        day_dec_base = pd.date_range(start='2014-12-31 0:00',  end='2014-12-31 23:00', freq='H')
        day_dec_copy_to = pd.date_range(start='2013-12-31 0:00',  end='2013-12-31 23:00', freq='H')

        # Add last day of previous year based on year downloaded from renewable ninjas
        solar_previous_day_of_year = pd.Series(solar_generation[day_jan_base].values, index=day_jan_copy_to)
        solar_generation = solar_generation.append(solar_previous_day_of_year)
        wind_previous_day_of_year = pd.Series(wind_generation[day_jan_base].values, index=day_jan_copy_to)
        wind_generation = wind_generation.append(wind_previous_day_of_year)

        # Add first day of following year based on year downloaded from renewable ninjas
        solar_following_day_of_year = pd.Series(solar_generation[day_dec_base].values, index=day_dec_copy_to)
        solar_generation = solar_generation.append(solar_following_day_of_year)
        wind_following_day_of_year = pd.Series(wind_generation[day_dec_base].values, index=day_dec_copy_to)
        wind_generation = wind_generation.append(wind_following_day_of_year)

        # Reindex solar_generation according to timeshift
        solar_generation = solar_generation.reindex(datetimerange_367 + pd.DateOffset(hours=time_zone_offset))
        wind_generation = wind_generation.reindex(datetimerange_367 + pd.DateOffset(hours=time_zone_offset))

        ########### Generate csv file ###########
        location_data_frame = pd.DataFrame({'Demand': demands[str(data_set_ids["NESP_ID"][name])].values,
                                           'SolarGen': solar_generation[datetimerange_local].values,
                                            'Wind': wind_generation[datetimerange_local].values}, index=datetimerange_local)

        location_data_frame.to_csv('../inputs/timeseries/nesp_' + str(data_set_ids["NESP_ID"][name]) + '.csv', index=False, sep=';')

        # Necessary wait for new server request (not to overload the server)
        time.sleep(72) # To reach 50/hr # Below 50 total profiles: 6/min = 10s sleep