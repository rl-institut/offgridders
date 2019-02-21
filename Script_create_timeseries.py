import pandas as pd
import requests
import time
import logging

logging.basicConfig(filename='./simulation_results/script_logfile.log',level=logging.DEBUG)

##########################
# Read project file      #
##########################
logging.info('Reading from excel sheet')
#file = '/home/local/RL-INSTITUT/martha.hoffmann/Downloads/Mastersheet.xlsx'
file = '/mnt/Storage/Documents/Studium/RLI/Masterthesis/ASEP_Test/project_data/Mastersheet.xlsx'
sheet = 'Data'
column = 2
data = pd.read_excel(file,
                     sheet_name=sheet,
                     index_col=column).transpose()

# add all index numbers of micro grid locations to be analysed to this list
list = [ 126, 53, 17, 105, 121, 107, 108, 34, 32, 20 ]

names = pd.Series([data[list[i]]['Grid Name'] for i in range(0,10)],
                        index=list)

lon_lat = pd.DataFrame([[data[list[i]]['X'] for i in range(0,10)],
                         [data[list[i]]['Y'] for i in range(0,10)]],
                        index=['lon', 'lat'],
                        columns=[list[i] for i in range(0,10)])

data = data.drop(index=['X',
                'Y',
                'Grid Name',
                'Main Islan',
                'Specific R',
                'Province',
                'OPERATING (SEP)',
                'Operating hours (Load profiles)',
                'Plant Operator',
                'Plant Owner Name',
                'Distributi',
                'Number of PP',
                'Rated capacity',
                'Dependable capacity',
                'Eff. (L/kWh)',
                'Fuel/Gross generation',
                'Fuel/Sales',
                'Liter/Gross',
                'Liter/Sales',
                'Peak Deman',
                'Mean Demand',
                'Peak/Mean Demand',
                'Rat. Cap/Peak',
                'Dep. cap/Peak',
                'Annual Ene',
                'Franchise Pop',
                'Barangays',
                'Study',
                'Load curve',
                'Length',
                'Potential',
                'Connected',
                'Residentia',
                'Commercial',
                'Industrial',
                'Public ins',
                'Street lig',
                'Irrigation',
                'Source'])

demands = pd.DataFrame([data[list[i]] for i in range(0, 10)]).transpose()

##########################
# Renewables Ninjas      #
##########################

logging.info('Get data from renewable ninjas:')

token = 'f8c619d5a5a227629019fa61c24ce7bcd3c70ab9'
api_base = 'https://www.renewables.ninja/api/'

s = requests.session()
# Send token header with each request
s.headers = {'Authorization': 'Token ' + token}

url_solar = api_base + 'data/pv'

# these dates have to be set as UTC, NOT LOCAL TIME.
# Otherwise wrong output (sun during night). Can be worked aroung with 'format': 'csv' and
# https://community.renewables.ninja/t/python-api-example-returning-error/218/7
# but not performed here
# HERE: -8 h in philippines

# implement this with ...
# time_zone_offset = 8
args_general = {
    'date_from': '2014-12-31',
    'date_to': '2015-12-31'}

# this could be made easier by loading csv, splitting by \n, splitting by , writing to csv and loading again with header set to column 2, th eone with local time.
datetimerange = pd.date_range(start='2014-12-31 16:00',  end='2015-12-31 15:00', freq='H')

args_pv = {
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
args_pv.update(args_general.copy())

url_wind = api_base + 'data/wind'

args_wind = {
    'capacity': 1.0,
    'height': 100,
    'turbine': 'Vestas V80 2000',
    'format': 'json',
    'metadata': False,
    'raw': False
}
args_wind.update(args_general.copy())

for location in list:
    print(names[location])
    logging.info('    Requesting for location: ' + str(location) + '/' + names[location])
    args_location = {
        'lat': lon_lat[location]['lat'],
        'lon': lon_lat[location]['lon']}
    ########### PV ##############
    args_pv.update(args_location.copy())
    r = s.get(url_solar, params=args_pv)
    if r.status_code == 429:
        print('Too many requests per minute')
    solar_generation = pd.read_json(r.text, orient='index')

    ########### Wind ###########
    args_wind.update(args_location.copy())
    r = s.get(url_wind, params=args_wind)
    if r.status_code == 429:
        print('Too many requests per minute')
    wind_generation = pd.read_json(r.text, orient='index')

    ########### Generate csv file ###########
    location_data_frame = pd.DataFrame({'Demand': demands[location].values,
                                       'SolarGen': solar_generation['output'][datetimerange].values,
                                        'Wind': wind_generation['output'][datetimerange].values}, index=demands.index)

    location_data_frame.to_csv('./inputs/timeseries/' + str(location) + '_' + names[location] + '.csv', index=False, sep=';')

    # Necessary wait 20 s for new server request (not to overload the server)
    time.sleep(20)