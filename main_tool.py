'''
Overlying script for tool for the analysis of possible
operational modes of micro grids interconnecting with an unreliable national grid
For efficient iterations? https://docs.python.org/2/library/itertools.html
'''


import pprint as pp
import timeit

from oemof.tools import logger
import logging
# Logging
logger.define_logging(logfile='main_tool.log',
                      screen_level=logging.INFO,
                      file_level=logging.DEBUG)

from cases import cases
#from national_grid import national_grid

###############################################################################
# Check for, create or empty results dictionary                               #
###############################################################################
from general_functions import config_func
config_func.check_results_dir()

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
demand_profiles = demand.get()

from input_values import white_noise_demand
if white_noise_demand != 0:
    from general_functions import helpers
    demand_profiles = helpers.noise_demand(white_noise_demand, demand_profiles)
#-------------------------------PV system-------------------------------------#
# Currently only based on generic data, specific panel/inverter               #
#-----------------------------------------------------------------------------#
from pvlib_scripts import pvgen
pv_generation_per_kWp = pvgen.get()

from input_values import white_noise_irradiation
if white_noise_irradiation != 0:
    from general_functions import helpers
    pv_generation_per_kWp = helpers.noise_pv(white_noise_irradiation, pv_generation_per_kWp)
#-----------------------------Sensitivity-------------------------------------#
# Sensitivity cases to be evaluated during the simulation                     #
# Attention: Right now, parameters influencing the OEM of the base case are   #
# included in an own loop. It would also be possible to merge those loops     #
# (point of attack: config_func.sensitivity_experiments)                      #
#-----------------------------------------------------------------------------#
from sensitivity import sensitivity
sensitivity_experiments, overall_results     =   sensitivity.experiments()
logging.info(str(len(sensitivity_experiments)) + ' simulations are necessary to perform the sensitivity analysis.')

#-------------------------------Blackouts-------------------------------------#
# Creating list of possible blackout scenarios (combinations of durations     #
# frequencies.                                                                #
# Creating events, that later on are constant for each case with spec. combi. #
#-----------------------------------------------------------------------------#

blackout_experiments   =   sensitivity.blackout_experiments()
logging.info(str(len(sensitivity_experiments)) + ' combinations of blackout duration and frequency will be analysed. \n')

# todo create module for retrieving blackout events at specific combination of duration/frequency
#blackout_events = { {d: XY, f: XY, pd.Dataframe},  } => from national_grid.availability(blackoutduration/100, blackoutfrequency/100)

#---------------------------- Base case OEM ----------------------------------#
# Based on demand, pv generation and subjected to sensitivity analysis SOEM   #
#-----------------------------------------------------------------------------#
from config import print_simulation_experiment
from general_functions import helpers

# todo show figures but continue script!
experiment_count= 0

for experiment in sensitivity_experiments:

    experiment_count = experiment_count + 1
    # ----------------------------Input data---------------------------------------#
    # Preprocessing of inputdata where necessary based on case                     #
    # -----------------------------------------------------------------------------#
    from general_functions import config_func
    experiment = config_func.input_data(experiment)

    # ----------------------------Base Case OEM------------------------------------#
    # Optimization of optimal capacities in base case (off-grid micro grid)        #
    # -----------------------------------------------------------------------------#
    # todo: this function should be called with base_experiment[] to include sensitivites
    logging.info('Starting simulation of base OEM, experiment no. ' + str(experiment_count) + '...')
    start = timeit.default_timer()
    results, capacities_base = cases.base_oem(demand_profiles[experiment['demand_profile']], pv_generation_per_kWp, experiment)
    duration = timeit.default_timer() - start
    logging.info('    Simulation of base OEM complete.')
    logging.info('    Simulation time (s): ' + str(round(duration, 2)) + '\n')
    overall_results = helpers.store_result_matrix(overall_results, 'base_oem', experiment, results, duration)

    ###############################################################################
    # Simulations of all cases
    ###############################################################################

    # todo: actually, calling all blackoutdurations/blackoutfrequencies seperately here is not helpful - the blackout
    # could be with check for frequency / duration and appropriate event

   # national_grid_availability = blackout_events['freq'=]['dur'=]

    ###############################################################################
    # Creating, simulating and storing micro grid energy systems with oemof
    # According to parameters set beforehand
    ###############################################################################
    for items in listof_cases:
        logging.info('Starting simulation of case ' + items + ', experiment no. ' + str(experiment_count) + '...')
        start = timeit.default_timer()
        if      items == 'mg_fixed':             oemof_results = cases.mg_fix(demand_profiles[experiment['demand_profile']], pv_generation_per_kWp, experiment, capacities_base)
        elif    items == 'buyoff':               cases.buyoff()
        elif    items == 'parallel':             cases.parallel()
        elif    items == 'adapted':              cases.adapted()
        elif    items == 'oem_interconnected':   cases.oem_interconnected()
        elif    items == 'backupgrid':           cases.backupgrid()
        elif    items == 'buysell':              cases.buysell()
        else: logging.warning("Unknown case!")
        duration = timeit.default_timer() - start
        logging.info('    Simulation of case '+items+' complete.')
        logging.info('    Simulation time (s): ' + str(round(duration, 2)) + '\n')
        # Create DataFrame with all data
        overall_results = helpers.store_result_matrix(overall_results, items, experiment, oemof_results, duration)

    pp.pprint(overall_results)
    if print_simulation_experiment == True:
        logging.info('The case with following parameters has been analysed:')
        pp.pprint(sensitivity_experiments)

    from config import output_folder
    # Writing DataFrame with all results to csv file
    overall_results.to_csv(output_folder + '/results.csv')

###############################################################################
# Plot all graphs
###############################################################################