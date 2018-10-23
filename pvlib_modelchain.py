'''
Requires 'tables' plugin
Utilizing modelchain
'''

import pandas as pd
import matplotlib.pyplot as plt
import pvlib
from pvlib.pvsystem import PVSystem
from pvlib.location import Location
from pvlib.modelchain import ModelChain

time_frame = pd.DatetimeIndex(start='2018', end='2019', freq='15min', tz='Etc/GMT-1')
location = Location(latitude=50, longitude=10, name='Berlin', altitude=34)
print(location)

# loading module and inverter specifications from SAM
sandia_modules = pvlib.pvsystem.retrieve_sam('SandiaMod')
sapm_inverters = pvlib.pvsystem.retrieve_sam('cecinverter')

# loading specific module and inverter parameters
module = sandia_modules['Canadian_Solar_CS5P_220M___2009_']
inverter = sapm_inverters['ABB__MICRO_0_25_I_OUTD_US_208_208V__CEC_2014_']
print(inverter)
print(module)

# constant ambient air temperature and wind speed for simplicity
system = PVSystem(surface_tilt=20, surface_azimuth=180,
                  module_parameters=module,
                  inverter_parameters=inverter, name='Berlin rooftop system')
                # single module/inverter parameters could also be used as input!

print(system)
mc = ModelChain(system, location)
print (mc)

weather = pd.DataFrame([[1050, 1000, 100, 30, 5]],
                       columns=['ghi', 'dni', 'dhi', 'temp_air', 'wind_speed'],
                       index=[pd.Timestamp('20180401 1200', tz='Etc/GMT-1')])
mc.run_model(times=weather.index, weather=weather)