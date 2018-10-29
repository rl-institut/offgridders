
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

class pvlib_scripts:
    # ####################################################################### #
    #        Calculation of general solar variables, based on location        #
    # ####################################################################### #
    def irradiation(pv_system_location, location_name, date_time_index):

        solpos = pvlib.solarposition.get_solarposition(date_time_index, pv_system_location.loc['latitude', location_name],
                                                       pv_system_location.loc['longitude', location_name])
        dni_extra = pvlib.irradiance.get_extra_radiation(date_time_index)
        airmass = pvlib.atmosphere.get_relative_airmass(solpos['apparent_zenith'])
        pressure = pvlib.atmosphere.alt2pres(pv_system_location.loc['altitude', location_name])
        am_abs = pvlib.atmosphere.get_absolute_airmass(airmass, pressure)
        tl = pvlib.clearsky.lookup_linke_turbidity(date_time_index, pv_system_location.loc['latitude', location_name],
                                                   pv_system_location.loc['longitude', location_name])  # requires installation of tables
        cs = pvlib.clearsky.ineichen(solpos['apparent_zenith'], am_abs, tl,
                                     dni_extra=dni_extra, altitude=pv_system_location.loc['altitude', location_name])

        logging.info('Calculated irradiation parameters dependent on location.')
        return solpos, dni_extra, airmass, pressure, am_abs, tl, cs

    # ########################################################################## #
    #      Calculation of irradiance, dc, ac power for one specific py system    #
    # ########################################################################## #
    def generation(pv_system_parameters, pv_composite_name, location_name, solpos, dni_extra, airmass, pressure, am_abs, tl, cs, date_time_index):
        # constant ambient air temperature and wind speed for simplicity
        temp_air = 20
        wind_speed = 0

        # loading module and inverter specifications from SAM
        sandia_modules = pvlib.pvsystem.retrieve_sam('SandiaMod')
        sapm_inverters = pvlib.pvsystem.retrieve_sam('cecinverter')

        # loading specific module and inverter parameters
        module = sandia_modules[pv_system_parameters.loc['module_name', pv_composite_name]]
        inverter = sapm_inverters[pv_system_parameters.loc['inverter_name', pv_composite_name]]

        aoi = pvlib.irradiance.aoi(pv_system_parameters.loc['tilt', pv_composite_name],
                                   pv_system_parameters.loc['surface_azimuth', pv_composite_name],
                                   solpos['apparent_zenith'], solpos['azimuth'])
        total_irrad = pvlib.irradiance.get_total_irradiance(pv_system_parameters.loc['tilt', pv_composite_name],
                                                            pv_system_parameters.loc['surface_azimuth', pv_composite_name],
                                                            solpos['apparent_zenith'],
                                                            solpos['azimuth'],
                                                            cs['dni'], cs['ghi'], cs['dhi'],
                                                            dni_extra=dni_extra,
                                                            model='haydavies')
        temps = pvlib.pvsystem.sapm_celltemp(total_irrad['poa_global'],
                                             wind_speed, temp_air)
        effective_irradiance = pvlib.pvsystem.sapm_effective_irradiance(
            total_irrad['poa_direct'], total_irrad['poa_diffuse'],
            am_abs, aoi, module)  # irradiation equal to the power being produced
        dc = pvlib.pvsystem.sapm(effective_irradiance, temps['temp_cell'], module)  # dc power in Wh
        ac = pvlib.pvsystem.snlinverter(dc['v_mp'], dc['p_mp'], inverter)  # ac power in Wh

        annual_energy_kWh = ac.sum()
        if date_time_index.freq == '15min':
            annual_energy_kWh = annual_energy_kWh / 4  # 15 min steps in timeframe

        energies = pd.Series(annual_energy_kWh)
        print("Annual energy from irradiation in kWh")
        print(energies.round(0))

        irradiation, = plt.plot(total_irrad['poa_global']/1000, label='Solar irradiation per sqm')
        pv_gen, = plt.plot(ac/1000, label='Panel generation: '+ pv_system_parameters.loc['module_name', pv_composite_name])
        plt.legend()
        plt.ylabel('kWh')
        plt.title('Solar irradiation and '+pv_composite_name+' panel generation')

        plt.show()

        logging.info('Calculated solar irradiation and pv generation (without white noise) for '+pv_composite_name+'_'+location_name)
        return ac/1000 # in kWh

# times = pd.DatetimeIndex(start='2018', end='2019', freq='15min')