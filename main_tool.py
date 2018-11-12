'''
Overlying script for tool for the analysis of possible
operational modes of micro grids interconnecting with an unreliable national grid
For efficient iterations? https://docs.python.org/2/library/itertools.html
'''

import os
import pandas as pd
import numpy as np

from oemof.tools import logger
import logging
# Logging
logger.define_logging(logfile='main_tool.log',
                      screen_level=logging.INFO,
                      file_level=logging.DEBUG)

from cases import cases
from national_grid import national_grid

###############################################################################
# Load previous simulation of base case or perform OEM for base case
###############################################################################



###############################################################################
# Create lists
###############################################################################

listof_cases =['base',
               'buyoff',
               'parallel',
               'adapted',
               'oem_interconnected',
               'backupgrid',
               'buysell',
               'mg_oem'
               ]

listof_plots=[]

listof_rankings=[]

dictof_oemparameters ={'cost_pv':      [100, 100, 5],
                       'cost_genset':  [100, 100, 5],
                       'cost_storage': [100, 100, 5],
                       'fuel_price_100':   [50, 50, 10],
                       'wacc_100':         [10, 10, 1],
                       'shortage':         [15, 15, 1]}

dictof_nooemparameters ={ 'blackout_duration_100':  [20, 20, 5],
                          'blackout_frequency_100': [90, 90, 10],
                          'distance_to_grid':   [10, 10, 5]}


###############################################################################
# Generation of initializing data (demand, pv generation, basecase capacities
###############################################################################
#-----------------------------Demand profile------------------------------#
from demand_profile import demand

demand_profile = demand.estimate()

#-----------------------------PV system------------------------------#
from pvlib_scripts import pvlib_scripts
from input_values import pv_system_location, location_name, pv_system_parameters, pv_composite_name
# Solar irradiance
solpos, dni_extra, airmass, pressure, am_abs, tl, cs = pvlib_scripts.irradiation(pv_system_location, location_name)
# PV generation
pv_generation_per_kWp, pv_module_kWp = pvlib_scripts.generation(pv_system_parameters, pv_composite_name, location_name, solpos, dni_extra, airmass, pressure, am_abs, tl, cs)

capacities = cases.mg_oem(demand_profile, pv_generation_per_kWp)

###############################################################################
# Simulations of all cases
###############################################################################
for distance_to_grid in range(dictof_nooemparameters['distance_to_grid'][0],
                              dictof_nooemparameters['distance_to_grid'][1]+1,
                              dictof_nooemparameters['distance_to_grid'][2]):

    print("distance to grid (km): " + str(distance_to_grid))

    for blackoutduration in range(dictof_nooemparameters['blackout_duration_100'][0],
                                   dictof_nooemparameters['blackout_duration_100'][1]+1,
                                   dictof_nooemparameters['blackout_duration_100'][2]):

        for blackoutfrequency in range(dictof_nooemparameters['blackout_frequency_100'][0],
                                       dictof_nooemparameters['blackout_frequency_100'][1]+1,
                                       dictof_nooemparameters['blackout_frequency_100'][2]):

            national_grid.availability(blackoutduration/100, blackoutfrequency/100)

            ###############################################################################
            # Creating, simulating and storing micro grid energy systems with oemof
            # According to parameters set beforehand
            ###############################################################################
            for items in listof_cases:
                if      items == 'base':                 cases.base(demand_profile, pv_generation_per_kWp)
                elif    items == 'buyoff':               cases.buyoff()
                elif    items == 'parallel':             cases.parallel()
                elif    items == 'adapted':              cases.adapted()
                elif    items == 'oem_interconnected':   cases.oem_interconnected()
                elif    items == 'backupgrid':           cases.backupgrid()
                elif    items == 'buysell':              cases.buysell()
                elif    items == 'mg_oem':               cases.mg_oem(demand_profile, pv_generation_per_kWp)
                else: logging.warning("Unknown case!")

            logging.debug("\n      All cases simulated for "+ str(blackoutduration/100) + "hrs blackout duration \n "
                         + "        with a blackout frequency of " + str(blackoutfrequency/100) + " per month \n"
                         + "        at a distance to the main grid of " + str(distance_to_grid) + " km.")

        logging.debug("\n      All cases simulated for blackout duration in range of " + str(dictof_nooemparameters['blackout_duration_100'][0]/100)
                     + " to " + str(dictof_nooemparameters['blackout_duration_100'][1]/100) + " hrs \n "
                     + "        with a blackout frequency of " + str(blackoutfrequency/100) + " per month \n"
                     + "        at a distance to the main grid of " + str(distance_to_grid) + " km.")

    logging.debug("\n      All cases simulated for blackout duration in range of " + str(dictof_nooemparameters['blackout_duration_100'][0]/100)
        + " to " + str(dictof_nooemparameters['blackout_duration_100'][1]/100) + " hrs \n"
        + "     at a blackout frequency in range of " + str(dictof_nooemparameters['blackout_frequency_100'][0]/100)
        + " to " + str(dictof_nooemparameters['blackout_frequency_100'][1]/100) + " per month, \n"
        + "     at a distance to the main grid of " + str(distance_to_grid) + " km.")

logging.info("\n      All cases simulated for blackout duration in range of " + str(dictof_nooemparameters['blackout_duration_100'][0]/100)
        + " to " + str(dictof_nooemparameters['blackout_duration_100'][1]/100) + " hrs \n "
        + "     at a blackout frequency in range of " + str(dictof_nooemparameters['blackout_frequency_100'][0]/100)
        + " to " + str(dictof_nooemparameters['blackout_frequency_100'][1]/100) + " per month \n "
        + "     at a distance to the main grid in range of " + str(dictof_nooemparameters['distance_to_grid'][0])
        + " to " + str(dictof_nooemparameters['distance_to_grid'][1]) + " km.")

###############################################################################
# Create DataFrame with all data
###############################################################################



###############################################################################
# Plot all graphs
###############################################################################