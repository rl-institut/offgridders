import pandas as pd
import requests
import time
import logging

#logging.basicConfig(filename='./simulation_results/script_logfile.log',level=logging.DEBUG)

class renewables_ninjas():

    def get_all(location_s):

        logging.info('Get data from renewable ninjas:')

        args_general = {
            'date_from': '2014-12-31',
            'date_to': '2015-12-31'}

        args_wind, url_wind, args_pv, url_solar, s = renewables_ninjas.init_url(args_general)

        for location in location_s:

            start = pd.Timestamp(args_general['date_from']) + pd.DateOffset(days=1) - pd.DateOffset(hours=location_s[location]['utc_offset'])
            end = pd.Timestamp(args_general['date_to']) + pd.DateOffset(days=1) - pd.DateOffset(hours=location_s[location]['utc_offset']+1)
            datetimerange = pd.date_range(start=start, end=end, freq='H')
            print(len(datetimerange))

            logging.info('    Requesting for location: ' + str(location))
            args_location = {
                'lat': location_s[location]['lat'],
                'lon': location_s[location]['lon']}
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
            dict = {
                'SolarGen': solar_generation['output'][datetimerange].values,
                'Wind': wind_generation['output'][datetimerange].values}

            if location_s[location]['demand_file']!=None:
                demands = 0
                dict.update({'Demand': demands[location].values})

            location_data_frame = pd.DataFrame(dict,
                                               index=pd.date_range(start='2014-12-31 16:00',
                                                                   end='2015-12-31 15:00',
                                                                   freq='H'))

            location_data_frame.to_csv('../inputs/timeseries/' + str(location) + '.csv',
                                       index=False, sep=';')

            # Necessary wait 20 s for new server request (not to overload the server)
            time.sleep(20)

        return

    def init_url(args_general):
        token = 'f8c619d5a5a227629019fa61c24ce7bcd3c70ab9'
        api_base = 'https://www.renewables.ninja/api/'

        s = requests.session()
        # Send token header with each request
        s.headers = {'Authorization': 'Token ' + token}

        url_solar = api_base + 'data/pv'

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
        return args_wind, url_wind, args_pv, url_solar, s

location_s = {'consumer_tier2': {'lon': 87.75,  'lat': 26.45, 'demand_file': None, 'utc_offset': 5}}

renewables_ninjas.get_all(location_s)