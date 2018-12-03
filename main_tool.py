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
# todo: maybe better to create overall_results with large empty dataframe for easier addition of new columns?
sensitivity_experiments, overall_results     =   sensitivity.experiments()
logging.info(str(len(sensitivity_experiments)) + ' simulations are necessary to perform the sensitivity analysis.')

#-------------------------------Blackouts-------------------------------------#
# Creating list of possible blackout scenarios (combinations of durations     #
# frequencies.                                                                #
# Creating events, that later on are constant for each case with spec. combi. #
#-----------------------------------------------------------------------------#

# Creating all possible blackout experiments (combinations of duration and frequency)
blackout_experiments   =   sensitivity.blackout_experiments()
logging.info(str(len(blackout_experiments)) + ' combinations of blackout duration and frequency will be analysed. \n')
# Calculation of grid_availability with randomized blackouts
from national_grid import national_grid
sensitivity_grid_availability, blackout_results = national_grid.get_blackouts(blackout_experiments)

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
    logging.info('Starting simulation of base OEM, experiment no. ' + str(experiment_count) + '...')
    start = timeit.default_timer()

    from config import base_case_with_min_loading
    if base_case_with_min_loading == False:
        # Performing base case OEM without minimal loading, therefore optimizing genset capacities
        results, capacities_base = cases.base_oem(demand_profiles[experiment['demand_profile']],
                                                  pv_generation_per_kWp, experiment)
    else:
        # Performing base case OEM WITH minimal loading, thus fixing generator capacities to peak demand
        results, capacities_base = cases.base_oem_min_loading(demand_profiles[experiment['demand_profile']],
                                                              pv_generation_per_kWp, experiment)

    duration = timeit.default_timer() - start
    logging.info('    Simulation of base OEM complete.')
    logging.info('    Simulation time (s): ' + str(round(duration, 2)) + '\n')
    overall_results = helpers.store_result_matrix(overall_results, 'base_oem', experiment, results, duration)

    ###############################################################################
    # Simulations of all cases
    ###############################################################################

    from sensitivity import sensitivity
    blackout_experiment_name = sensitivity.blackout_experiment_name(experiment)
    grid_availability = sensitivity_grid_availability[blackout_experiment_name]
    ###############################################################################
    # Creating, simulating and storing micro grid energy systems with oemof
    # According to parameters set beforehand
    ###############################################################################
    for items in listof_cases:
        logging.info('Starting simulation of case ' + items + ', experiment no. ' + str(experiment_count) + '...')
        start = timeit.default_timer()
        if      items == 'offgrid_fixed':
            oemof_results = \
                cases.offgrid_fix(demand_profiles[experiment['demand_profile']], pv_generation_per_kWp, experiment, capacities_base)
        elif    items == 'interconnected_buy':
            oemof_results =\
                cases.interconnected_buy(demand_profiles[experiment['demand_profile']], pv_generation_per_kWp, experiment,
                                     capacities_base, grid_availability)

        elif    items == 'interconnected_buysell':
            oemof_results =\
                cases.interconnected_buysell(demand_profiles[experiment['demand_profile']], pv_generation_per_kWp, experiment,
                                         capacities_base, grid_availability)

        elif    items == 'buyoff':               cases.buyoff()
        elif    items == 'parallel':             cases.parallel()
        elif    items == 'adapted':              cases.adapted()
        elif    items == 'oem_interconnected':   cases.oem_interconnected()
        elif    items == 'backupgrid':           cases.backupgrid()
        else: logging.warning("Unknown case!")
        duration = timeit.default_timer() - start
        logging.info('    Simulation of case '+items+' complete.')
        logging.info('    Simulation time (s): ' + str(round(duration, 2)) + '\n')
        # Extend oemof_results by blackout characteristics
        print(blackout_results[blackout_experiment_name])
        oemof_results   = national_grid.extend_oemof_results(oemof_results, blackout_results[blackout_experiment_name])
        # Extend overall results dataframe with simulation results
        overall_results = helpers.store_result_matrix(overall_results, items, experiment, oemof_results, duration)

    if print_simulation_experiment == True:
        logging.info('The case with following parameters has been analysed:')
        pp.pprint(sensitivity_experiments)

    from config import output_folder
    # Writing DataFrame with all results to csv file
    overall_results.to_csv(output_folder + '/results.csv')

# display all results
pp.pprint(overall_results)
###############################################################################
# Plot all graphs
###############################################################################