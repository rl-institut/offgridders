'''
Overlying script for tool for the analysis of possible
operational modes of micro grids interconnecting with an unreliable national grid
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
               'buysell'
               ]

listof_plots=[]

listof_rankings=[]

dictof_oemparameters ={'cost_pv':      [100,100, 5],
                       'cost_genset':  [100, 100, 5],
                       'cost_storage': [100, 100, 5],
                       'fuel_price_100':   [50, 100, 10],
                       'wacc_100':         [10, 10, 1]}

dictof_nooemparameters ={ 'blackout_duration_100':  [20, 20, 5],
                          'blackout_frequency_100': [90, 110, 10],
                          'distance_to_grid':   [10, 15, 5]}

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

            for items in listof_cases:
                if      items == 'base':                 cases.base()
                elif    items == 'buyoff':               cases.buyoff()
                elif    items == 'parallel':             cases.parallel()
                elif    items == 'adapted':              cases.adapted()
                elif    items == 'oem_interconnected':   cases.oem_interconnected()
                elif    items == 'backupgrid':           cases.backupgrid()
                elif    items == 'buysell':              cases.buysell()
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