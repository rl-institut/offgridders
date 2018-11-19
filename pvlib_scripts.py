'''
Integrated version
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

# Import simulation settings
from config import date_time_index, display_graphs_solar
from general_functions import helpers

class pvgen:

    def get():
        from config import use_input_file_weather, date_time_index
        if use_input_file_weather == True:
            pv_generation_per_kWp = pvgen.read_from_file()
        else:
            from input_values import pv_system_location, location_name, pv_system_parameters, pv_composite_name
            # Solar irradiance
            solpos, dni_extra, airmass, pressure, am_abs, tl, cs = pvgen.pvlib_irradiation(pv_system_location,
                                                                                           location_name)
            # PV generation
            pv_generation_per_kWp, pv_module_kWp = pvgen.pvlib_generation(
                pv_system_parameters, pv_composite_name, location_name, solpos, dni_extra, airmass, pressure, am_abs, tl,
                cs)
        return pv_generation_per_kWp[date_time_index]

    # ####################################################################### #
    #        Read weather data from file                                      #
    # ####################################################################### #

    # todo current place of work
    def read_from_file():
        from input_values import input_file_weather
        from config import date_time_index
        data_set = pd.read_csv(input_file_weather, header=1)
        # todo not sure if this works!
        index = pd.DatetimeIndex(data_set['local_time'].values) + pd.DateOffset(year=date_time_index[0].year)
        pv_generation_per_kWp =  pd.Series(data_set['output'].values, index = index)
        # todo Actually, there needs to be a check for timesteps here
        logging.info('     Total annual pv generation at project site (kWh/a/kWp): ' + str(round(pv_generation_per_kWp.sum())))
        helpers.plot_results(pv_generation_per_kWp[date_time_index], "PV generation at project site",
                        "Date",
                        "Power kW")
        return pv_generation_per_kWp[date_time_index]


    # ####################################################################### #
    #        Calculation of general solar variables, based on location        #
    # ####################################################################### #
    def pvlib_irradiation(pv_system_location, location_name):

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
    def pvlib_generation(pv_system_parameters, pv_composite_name, location_name, solpos, dni_extra, airmass, pressure, am_abs, tl, cs):
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
        dc = pvlib.pvsystem.sapm(effective_irradiance, temps['temp_cell'], module)  # dc power per panel in Wh
        ac_per_panel = pvlib.pvsystem.snlinverter(dc['v_mp'], dc['p_mp'], inverter)  # ac power per panel in Wh

        #logging.info('PV Module: Maximum power current: ' + str(module.loc['Impo']) + ', maximum power voltage: ' + str(module.loc['Vmpo']))
        module_Wp=module.loc['Impo']*module.loc['Vmpo']
        logging.info('One PV Module offers ' + str(round(module_Wp)) + ' Wp')

        ac_per_kWp = ac_per_panel * 1000/module_Wp # ac power per installed kWp in Wh

        annual_energy_kWh = ac_per_kWp.sum()/1000
        if date_time_index.freq == '15min':
            annual_energy_kWh = annual_energy_kWh / 4  # 15 min steps in timeframe

        #energies = pd.Series(annual_energy_kWh)
        logging.debug('Annual energy from irradiation in kWh per kWp installed capacity' + str(round(annual_energy_kWh, 2)))

        if display_graphs_solar==True:
            irradiation, = plt.plot(total_irrad['poa_global']/1000, label='Solar irradiation per sqm')
            pv_gen1, = plt.plot(ac_per_kWp /1000,
                               label='Generation per installed kWp: ' + pv_system_parameters.loc['module_name', pv_composite_name])
            pv_gen2, = plt.plot(ac_per_panel/1000, label='Generation per panel: '+ pv_system_parameters.loc['module_name', pv_composite_name])
            plt.legend()
            plt.ylabel('kWh')
            plt.title('Solar irradiation and '+pv_composite_name+' panel generation')
            plt.show()

        logging.info('Calculated solar irradiation and pv generation (without white noise) for '+pv_composite_name+'_'+location_name)
        pv_generation_per_kWp = ac_per_kWp.clip_lower(0)/1000, module_Wp/1000  # pro installed kWp # clips all negative values!
        return pv_generation_per_kWp

# times = pd.DatetimeIndex(start='2018', end='2019', freq='15min')