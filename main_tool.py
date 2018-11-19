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
from general_functions import config_func
listof_cases        =   config_func.cases()

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
pv_generation_per_kWp, pv_module_kWp = pvlib_scripts.generation(
    pv_system_parameters, pv_composite_name, location_name, solpos, dni_extra, airmass, pressure, am_abs, tl, cs)

#-----------------------------Sensitivity-------------------------------------#
# Sensitivity cases to be evaluated during the simulation                     #
# Attention: Right now, parameters influencing the OEM of the base case are   #
# included in an own loop. It would also be possible to merge those loops     #
# (point of attack: config_func.sensitivity_experiments)                      #
#-----------------------------------------------------------------------------#
from sensitivity import sensitivity
from input_values import sensitivity_bounds, sensitivity_constants

sensitivity_experiments     =   sensitivity.experiments(sensitivity_bounds,sensitivity_constants)
logging.info(str(len(sensitivity_experiments)) + ' simulations are necessary to perform the sensitivity analysis.')

#-------------------------------Blackouts-------------------------------------#
# Creating list of possible blackout scenarios (combinations of durations     #
# frequencies.                                                                #
# Creating events, that later on are constant for each case with spec. combi. #
#-----------------------------------------------------------------------------#

blackout_experiments   =   sensitivity.blackout_experiments(sensitivity_bounds, sensitivity_constants)
logging.info(str(len(sensitivity_experiments)) + ' combinations of blackout duration and frequency will be analysed.')

# todo create module for retrieving blackout events at specific combination of duration/frequency
#blackout_events = { {d: XY, f: XY, pd.Dataframe},  } => from national_grid.availability(blackoutduration/100, blackoutfrequency/100)

#---------------------------- Base case OEM ----------------------------------#
# Based on demand, pv generation and subjected to sensitivity analysis SOEM   #
#-----------------------------------------------------------------------------#
from config import print_simulation_experiment
for experiment in sensitivity_experiments:
    # todo: this function should be called with base_experiment[] to include sensitivites
    capacities_base = cases.base_oem(demand_profile, pv_generation_per_kWp, experiment)
    ###############################################################################
    # Simulations of all cases
    ###############################################################################

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
        if      items == 'mg_fixed':             cases.mg_fix(demand_profile, pv_generation_per_kWp, experiment, capacities_base)
        elif    items == 'buyoff':               cases.buyoff()
        elif    items == 'parallel':             cases.parallel()
        elif    items == 'adapted':              cases.adapted()
        elif    items == 'oem_interconnected':   cases.oem_interconnected()
        elif    items == 'backupgrid':           cases.backupgrid()
        elif    items == 'buysell':              cases.buysell()
        #elif    items == 'mg_oem':               cases.mg_oem(demand_profile, pv_generation_per_kWp, experiment['filename']) # which case is this supposed anyway?
        else: logging.warning("Unknown case!")

    if print_simulation_experiment == True:
        logging.info('The case with following parameters has been analysed:')
        pp.pprint(sensitivity_experiments)

###############################################################################
# Create DataFrame with all data
###############################################################################



###############################################################################
# Plot all graphs
###############################################################################