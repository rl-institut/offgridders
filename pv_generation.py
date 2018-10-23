# -*- coding: utf-8
"""
STANDALONE VERSION
Based on file from:
https://github.com/oemof/feedinlib/blob/dev/example/feedinlib_example_new.py#L111
Feedinlib documentation:
https://feedinlib.readthedocs.io/en/stable/index.html
"""

try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

import pvlib
import logging
from pvlib.pvsystem import PVSystem
from pvlib.location import Location
from pvlib.modelchain import ModelChain
from pvlib.tools import cosd
import feedinlib.weather as weather

logging.getLogger().setLevel(logging.INFO)

input_file_weather = './inputs/weather.csv'

# loading feedinlib's weather data
my_weather = weather.FeedinWeather()
my_weather.read_feedinlib_csv(input_file_weather)

# #####################################
# ********** pvlib ********************
# #####################################

# todo weatherdata includes dhi etc, but can this info be downloaded automatically from nasa??
# preparing the weather data to suit pvlib's needs
# different name for the wind speed
my_weather.data.rename(columns={'v_wind': 'wind_speed'}, inplace=True)
# temperature in degree Celsius instead of Kelvin
my_weather.data['temp_air'] = my_weather.data.temp_air - 273.15
# calculate ghi
my_weather.data['ghi'] = my_weather.data.dirhi + my_weather.data.dhi
w = my_weather.data

# time index from weather data set
times = my_weather.data.index

# get module and inverter parameter from sandia database
# todo read module and inverter lists -> identify which can be used at all
sandia_modules = pvlib.pvsystem.retrieve_sam('SandiaMod')
sapm_inverters = pvlib.pvsystem.retrieve_sam('sandiainverter')

# own module parameters
invertername = 'ABB__MICRO_0_25_I_OUTD_US_208_208V__CEC_2014_'
yingli210 = {
    'module_parameters': sandia_modules['Yingli_YL210__2008__E__'],
    'inverter_parameters': sapm_inverters[invertername],
    'surface_azimuth': 180,
    'surface_tilt': 60,
    'albedo': 0.2,
    }

# own location parameter
wittenberg = {
    'altitude': 34,
    'name': 'Wittenberg',
    'latitude': my_weather.latitude,
    'longitude': my_weather.longitude,
    }

# the following has been implemented in the pvlib ModelChain in the
# complete_irradiance method (pvlib version > v0.4.5)
if w.get('dni') is None:
    w['dni'] = (w.ghi - w.dhi) / cosd(
        Location(**wittenberg).get_solarposition(times).zenith)

# pvlib's ModelChain
mc = ModelChain(PVSystem(**yingli210),
                Location(**wittenberg),
                orientation_strategy='south_at_latitude_tilt')

mc.run_model(times, weather=w)

if plt:
    mc.dc.p_mp.fillna(0).plot()
    plt.show()
else:
    logging.warning("No plots shown. Install matplotlib to see the plots.")

logging.info('Done!')