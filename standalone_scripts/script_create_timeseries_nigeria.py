import pandas as pd
import requests
import matplotlib.pyplot as plt
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
path = "/home/local/RL-INSTITUT/martha.hoffmann/Desktop/Nigeria/Nigeria_EnergyData_Plateau.csv"
#path = "/mnt/Storage/Documents/Studium/RLI/Masterthesis/Nigeria_Data/Nigeria_EnergyData_Plateau.csv"
data_set_ids = pd.read_csv(path, sep=';')

locations = data_set_ids[['NESP_ID', 'Lat', 'Lon']]
number_of_locations = len(locations.index)

path = "/home/local/RL-INSTITUT/martha.hoffmann/Desktop/Nigeria/.demand_profiles_nigeria_plateau.csv.~5dc73ba2"
demands = pd.read_csv(path, sep=',').drop(['Unnamed: 0'], axis=1)
logging.info('Get data from renewable ninjas:')
#demands.plot()
#plt.show()

tokens = [
    'f8c619d5a5a227629019fa61c24ce7bcd3c70ab9',
    '3503dce988ad11c4b5e479514505b932e3ca27b7']


api_base = 'https://www.renewables.ninja/api/'

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

count = 0
total_count = 0
token_number = 0

for item in locations.index:
    total_count += 1
    if token_number >= len(tokens):
        token_number = 0

    if count == len(tokens)*25:
        time.sleep(0)
        count = 0

    if os.path.isfile('../inputs/timeseries/nesp_' + str(data_set_ids["NESP_ID"][item]) + '.csv'):
        logging.info ('Timeseries for location ' + str(data_set_ids["NESP_ID"][item]) + ' already created (' + str(total_count) + '/' + str(number_of_locations) + ').')

    else:
        try:
            # Necessary wait for new server request (not to overload the server)
            time.sleep(60*60/(50))  # To reach 50/hr # Below 50 total profiles: 6/min = 10s sleep
            count += 1

            s = requests.session()
            s.headers = {'Authorization': 'Token ' + tokens[token_number]}
            token_number += 1

            logging.info('Requesting data for location ' + str(data_set_ids["NESP_ID"][item]) + ' (' + str(total_count) + '/' + str(number_of_locations) + ')')
            args_location = {
                'lat': locations['Lat'][item],
                'lon': locations['Lon'][item]}

            ########### PV ##############
            args_pv.update(args_location.copy())
            r = s.get(url_solar, params=args_pv)
            if r.status_code == 429:
                logging.info('Too many requests per minute/hour (PV)')
            solar_generation = pd.read_json(r.text, orient='index')
            solar_generation = solar_generation['output']

            ########### Wind ###########
            args_wind.update(args_location.copy())
            r = s.get(url_wind, params=args_wind)
            if r.status_code == 429:
                logging.info('Too many requests per minute/hour (Wind)')
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
            if str(data_set_ids["NESP_ID"][item]) == "3728":
                demands[str(data_set_ids["NESP_ID"][item])].plot
                plt.show()
            ########### Generate csv file ###########
            location_data_frame = pd.DataFrame({'Demand': demands[str(data_set_ids["NESP_ID"][item])].values,
                                               'SolarGen': solar_generation[datetimerange_local].values,
                                                'Wind': wind_generation[datetimerange_local].values}, index=datetimerange_local)

            location_data_frame.to_csv('../inputs/timeseries/nesp_' + str(data_set_ids["NESP_ID"][item]) + '.csv', index=False, sep=';')

        except (ValueError, TypeError):
            logging.info('Data not fetched!')