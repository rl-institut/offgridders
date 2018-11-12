'''
Overlying script for tool for the analysis of possible
operational modes of micro grids interconnecting with an unreliable national grid
For efficient iterations? https://docs.python.org/2/library/itertools.html
'''

import os
import pandas as pd
import numpy as np
import pprint as pp

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

# Not coded jet

###############################################################################
# Create lists
###############################################################################
#-------------------------------Cases-----------------------------------------#
# Cases to be evaluated during simulation                                     #
#-----------------------------------------------------------------------------#
from config_functions import config_func

listof_cases        =   config_func.cases()

#-----------------------------Sensitivity-------------------------------------#
# Sensitivity cases to be evaluated during the simulation                     #
# Attention: Right now, parameters influencing the OEM of the base case are   #
# included in an own loop. It would also be possible to merge those loops     #
# (point of attack: config_func.sensitivity_experiments)                      #
#-----------------------------------------------------------------------------#
from input_values import s_oem, s_nooem

oem_experiments     =   config_func.sensitivity_experiments(s_oem['sensitivity_bounds'], s_oem['constant_values'])
print(oem_experiments)
logging.info(str(len(oem_experiments)) + ' simulations are necessary to perform the sensitivity analysis for the base case.')

nooem_experiments   =   config_func.sensitivity_experiments(s_nooem['sensitivity_bounds'], s_nooem['constant_values'])
logging.info(str(len(nooem_experiments)) + ' simulations are necessary to perform the general sensitivity analysis.')

###############################################################################
# Generation of initializing data (demand, pv generation)
###############################################################################
#-----------------------------Demand profile----------------------------------#
# If demand profile is supposed to be subjected to sensitivity analysis as    #
# well, additional action has to be applied                                   #
#-----------------------------------------------------------------------------#
from demand_profile import demand
demand_profile = demand.estimate()

#-------------------------------PV system-------------------------------------#
# Currently only based on generic data, specific panel/inverter               #
#-----------------------------------------------------------------------------#
from pvlib_scripts import pvlib_scripts
from input_values import pv_system_location, location_name, pv_system_parameters, pv_composite_name
# Solar irradiance
solpos, dni_extra, airmass, pressure, am_abs, tl, cs = pvlib_scripts.irradiation(pv_system_location, location_name)
# PV generation
pv_generation_per_kWp, pv_module_kWp = pvlib_scripts.generation(pv_system_parameters, pv_composite_name, location_name, solpos, dni_extra, airmass, pressure, am_abs, tl, cs)

#-------------------------------Blackouts-------------------------------------#
# Creating list of possible blackout scenarios (combinations of durations     #
# frequencies.                                                                #
# Creating events, that later on are constant for each case with spec. combi. #
#-----------------------------------------------------------------------------#
blackout_experiments   =   config_func.blackout_sensitivity(s_nooem['sensitivity_bounds'], s_nooem['constant_values'])

#blackout_events = { {d: XY, f: XY, pd.Dataframe},  } => from national_grid.availability(blackoutduration/100, blackoutfrequency/100)

#---------------------------- Base case OEM ----------------------------------#
# Based on demand, pv generation and subjected to sensitivity analysis SOEM   #
#-----------------------------------------------------------------------------#
for base_experiments in oem_experiments:
    # todo: this function should be called with base_experiment[] to include sensitivites
    base_capacities = cases.mg_oem(demand_profile, pv_generation_per_kWp)

    ###############################################################################
    # Simulations of all cases
    ###############################################################################

    for sensitivity_experiments in nooem_experiments:
        # todo: info in sensitivity parameters should be included here
        # todo: actually, calling all blackoutdurations/blackoutfrequencies seperately here is not helpful - the blackout
        # incidents are not constant between cases with same bd/bf. workaround?
        # could be with check for frequency / duration and appropriate event

       # national_grid_availability = blackout_events['freq'=]['dur'=]

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

        pp.pprint(sensitivity_experiments)

    pp.pprint(base_experiments)

###############################################################################
# Create DataFrame with all data
###############################################################################



###############################################################################
# Plot all graphs
###############################################################################