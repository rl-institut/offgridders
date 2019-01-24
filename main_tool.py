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

###############################################################################
# Get values from excel_template:                                             #
# * Experiments: Settings, project sites                                      #
# * List of simulated cases                                                   #
###############################################################################
#-------- Get all settings ---------------------------------------------------#
settings, parameters_constant_values, parameters_sensitivity, project_sites, case_definitions = excel_template.settings()

#-------- Define all experiments, define result parameters -------------------#
from sensitivity_new import sensitvitiy_experiments
experiments, title_overall_results = sensitvitiy_experiments.get(settings, parameters_constant_values, parameters_sensitivity, project_sites, case_definitions)

###############################################################################
# Process and initialize        #
###############################################################################
#-------- Check for, create or empty results directory -----------------------#
from output_functions import output
output.check_output_directory()

#-------- Generate list of cases analysed in simulation ----------------------#
from process_input import process_input_parameters as process_input
case_list = process_input.list_of_cases(case_definitions)

#-------- Extend experiments with input time series
#-------- (demand, pv_generation_per_kWp, wind_generation_per_kW)
from read_from_files import csv_input
project_site_timeseries(experiments, project_sites)

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

    demand_profile_experiment =  demand_profiles[experiment['demand_profile']]

    from sensitivity import sensitivity
    blackout_experiment_name = sensitivity.blackout_experiment_name(experiment)
    grid_availability = sensitivity_grid_availability[blackout_experiment_name]

    # ----------------------------Base Case OEM------------------------------------#
    # Optimization of optimal capacities in base case (off-grid micro grid)        #
    # -----------------------------------------------------------------------------#
    logging.info('Starting simulation of base OEM, experiment no. ' + str(experiment_count) + '...')
    start = timeit.default_timer()

    from config import base_case_with_min_loading
    from oemof_simulate import oemof_simulate
    if base_case_with_min_loading == False:
        # Performing base case OEM without minimal loading, therefore optimizing genset capacities
        # get case definition
        case_dict = cases.get_case_dict('base_oem', experiment, demand_profile_experiment, capacities_base=None)
        # run oemof model
        oemof_results = oemof_simulate.run(experiment, case_dict, demand_profile_experiment, pv_generation_per_kWp,
                                                 grid_availability)
    else:
        # Performing base case OEM WITH minimal loading, thus fixing generator capacities to peak demand
        # todo currently not operational!
        oemof_results = cases.base_oem_min_loading(demand_profile_experiment, pv_generation_per_kWp, experiment, grid_availability)

    capacities_base = helpers.define_base_capacities(oemof_results)

    duration = timeit.default_timer() - start
    logging.info('    Simulation of base OEM complete.')
    logging.info('    Simulation time (s): ' + str(round(duration, 2)) + '\n')
    overall_results = helpers.store_result_matrix(overall_results, experiment, oemof_results, duration)

    ###############################################################################
    # Simulations of all cases
    ###############################################################################
    for items in listof_cases:
        # todo define all this in sumulate.run! extract simulation time from oemof results?
        logging.info('Starting simulation of case ' + items + ', experiment no. ' + str(experiment_count) + '...')
        start = timeit.default_timer()
        ###############################################################################
        # Creating, simulating and storing micro grid energy systems with oemof
        # According to parameters set beforehand
        ###############################################################################
        # get definitions for cases
        case_dict = cases.get_case_dict(items, experiment, demand_profile_experiment, capacities_base)
        # run oemof model
        oemof_results = oemof_simulate.run(experiment, case_dict, demand_profile_experiment, pv_generation_per_kWp,
                                                     grid_availability)
        # Extend oemof_results by blackout characteristics
        oemof_results   = national_grid.extend_oemof_results(oemof_results, blackout_results[blackout_experiment_name])
        # Extend overall results dataframe with simulation results
        overall_results = helpers.store_result_matrix(overall_results, experiment, oemof_results, duration)

        duration = timeit.default_timer() - start
        logging.info('    Simulation of case '+items+' complete.')
        logging.info('    Simulation time (s): ' + str(round(duration, 2)) + '\n')

    if print_simulation_experiment == True:
        logging.info('The experiment with following parameters has been analysed:')
        pp.pprint(sensitivity_experiments)

    from config import output_folder
    # Writing DataFrame with all results to csv file
    overall_results.to_csv(output_folder + '/results.csv')

# display all results
pp.pprint(overall_results)
###############################################################################
# Plot all graphs
###############################################################################