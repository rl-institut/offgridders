
'''
STANDALONE Version
Requires 'tables' plugin
This is the long version, but much of this can be packaged in the Modelchain
'''

import pandas as pd
import pvlib

import logging
logging.getLogger().setLevel(logging.INFO)

try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None
    logging.warning("Install matplotlib to plot graphs!")

latitude = 50
longitude = 10
location_name = 'Berlin'
altitude = 34
timezone = 'Etc/GMT-1'

surface_azimuth = 180
tilt = 0

times = pd.DatetimeIndex(start='2018', end='2019', freq='15min')

# loading module and inverter specifications from SAM
sandia_modules = pvlib.pvsystem.retrieve_sam('SandiaMod')
sapm_inverters = pvlib.pvsystem.retrieve_sam('cecinverter')

# loading specific module and inverter parameters
module = sandia_modules['Canadian_Solar_CS5P_220M___2009_']
inverter = sapm_inverters['ABB__MICRO_0_25_I_OUTD_US_208_208V__CEC_2014_']

# constant ambient air temperature and wind speed for simplicity
temp_air = 20
wind_speed = 0

# system definition
system = {'module': module,
          'inverter': inverter,
          'surface_azimuth': surface_azimuth,
          'surface_tilt': tilt}

# ################################################# #
#      Calculation of irradiance, dc, ac power      #
# ################################################# #

solpos = pvlib.solarposition.get_solarposition(times, latitude, longitude)
dni_extra = pvlib.irradiance.get_extra_radiation(times)
airmass = pvlib.atmosphere.get_relative_airmass(solpos['apparent_zenith'])
pressure = pvlib.atmosphere.alt2pres(altitude)
am_abs = pvlib.atmosphere.get_absolute_airmass(airmass, pressure)
tl = pvlib.clearsky.lookup_linke_turbidity(times, latitude, longitude) # requires installation of tables
cs = pvlib.clearsky.ineichen(solpos['apparent_zenith'], am_abs, tl,
                             dni_extra=dni_extra, altitude=altitude)
aoi = pvlib.irradiance.aoi(system['surface_tilt'], system['surface_azimuth'],
                           solpos['apparent_zenith'], solpos['azimuth'])
total_irrad = pvlib.irradiance.get_total_irradiance(system['surface_tilt'],
                                                    system['surface_azimuth'],
                                                    solpos['apparent_zenith'],
                                                    solpos['azimuth'],
                                                    cs['dni'], cs['ghi'], cs['dhi'],
                                                    dni_extra=dni_extra,
                                                    model='haydavies')
temps = pvlib.pvsystem.sapm_celltemp(total_irrad['poa_global'],
                                     wind_speed, temp_air)
effective_irradiance = pvlib.pvsystem.sapm_effective_irradiance(
    total_irrad['poa_direct'], total_irrad['poa_diffuse'],
    am_abs, aoi, module) # irradiation equal to the power being produced
dc = pvlib.pvsystem.sapm(effective_irradiance, temps['temp_cell'], module) # dc power
ac = pvlib.pvsystem.snlinverter(dc['v_mp'], dc['p_mp'], inverter) # ac power
annual_energy = ac.sum()/4 # 15 min steps in timeframe
annual_energy_kWh = annual_energy/1000

energies = pd.Series(annual_energy_kWh)
print("Annual energy from irradiation in kWh")
print(energies.round(0))

total_irrad['poa_global'].plot()
ac.plot()
plt.ylabel('Power (kW)')
plt.show()

logging.info('Calculated solar irradiation and pv generation (without white noise).')