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
from B_read_from_files import excel_template
settings, parameters_constant_values, parameters_sensitivity, project_site_s, case_definitions = excel_template.settings()

#-------- Define all sensitivity_experiment_s, define result parameters -------------------#
from C_sensitivity_experiments import generate_sensitvitiy_experiments, get_names
sensitivity_experiment_s, blackout_experiment_s, title_overall_results = generate_sensitvitiy_experiments.get(settings, parameters_constant_values, parameters_sensitivity, project_site_s)

###############################################################################
# Process and initialize        #
###############################################################################
#-------- Check for, create or empty results directory -----------------------#
from Z_output_functions import output
output.check_output_directory(sensitivity_experiment_s)

#-------- Generate list of cases analysed in simulation ----------------------#
# missing process input: date time frame -> does it make more sense to keep settings konstant and give to each function or increase disc volume by having it for EACH EXPERIMENT?
from D_process_input import process_input_parameters as process_input
case_list = process_input.list_of_cases(case_definitions)

#----------------- Extend sensitivity_experiment_s----------------------------#
# with demand, pv_generation_per_kWp, wind_generation_per_kW                  #
#-----------------------------------------------------------------------------#
from B_read_from_files import csv_input
max_date_time_index, max_evaluated_days = csv_input.project_site_timeseries(sensitivity_experiment_s, project_site_s)
settings.update({'date_time_index': max_date_time_index})
settings.update({'evaluated_days': max_evaluated_days})

# Apply noise
from D_process_input import noise
noise.apply(sensitivity_experiment_s)

# Calculation of grid_availability with randomized blackouts
from E_blackouts_central_grid import central_grid
sensitivity_grid_availability, blackout_results = central_grid.get_blackouts(settings, blackout_experiment_s)

#---------------------------- Base case OEM ----------------------------------#
# Based on demand, pv generation and subjected to sensitivity analysis SOEM   #
#-----------------------------------------------------------------------------#
# import all scripts necessary for loop
from Z_general_functions import helpers
from G0_oemof_simulate import oemof_simulate

# todo show figures but continue script!
experiment_count= 0

for experiment in sensitivity_experiment_s:

    experiment_count = experiment_count + 1

    demand_profile_experiment =  sensitivity_experiment_s[experiment]['demand_profile']
    pv_generation_per_kWp = sensitivity_experiment_s[experiment]['pv_generation_per_kWp']

    blackout_experiment_name = get_names.blackout_experiment_name(sensitivity_experiment_s[experiment])
    grid_availability = sensitivity_grid_availability[blackout_experiment_name]

    # ----------------------------Base Case OEM------------------------------------#
    # Optimization of optimal capacities in base case (off-grid micro grid)        #
    # -----------------------------------------------------------------------------#
    logging.info('Starting simulation of base OEM, experiment no. ' + str(experiment_count) + '...')
    start = timeit.default_timer()


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
    # Simulations of all cases                                                    #
    # first the ones defining base capacities, then the others                    #
    ###############################################################################
    for items in case_list:
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
        oemof_results   = central_grid.extend_oemof_results(oemof_results, blackout_results[blackout_experiment_name])
        # Extend overall results dataframe with simulation results
        overall_results = helpers.store_result_matrix(overall_results, experiment, oemof_results, duration)

        duration = timeit.default_timer() - start
        logging.info('    Simulation of case '+items+' complete.')
        logging.info('    Simulation time (s): ' + str(round(duration, 2)) + '\n')

    if experiment['print_simulation_experiment'] == True:
        logging.info('The experiment with following parameters has been analysed:')
        pp.pprint(sensitivity_experiment_s)

    # Writing DataFrame with all results to csv file
    overall_results.to_csv(experiment['output_folder'] + '/results.csv')

# display all results
pp.pprint(overall_results)
###############################################################################
# Plot all graphs
###############################################################################