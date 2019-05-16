'''
Overlying script for tool for the analysis of possible
operational modes of micro grids interconnecting with an unreliable national grid
For efficient iterations? https://docs.python.org/2/library/itertools.html
'''


import pprint as pp
import os, sys
from oemof.tools import logger
import logging
# Logging

logger.define_logging(logpath='./',
                      logfile='micro_grid_design_logfile.log',
                      screen_level=logging.INFO,
                      #screen_level=logging.DEBUG,
                      file_level=logging.DEBUG)

logging.info('\n \n MICRO GRID TOOL 2.1 '
             '\n Version: 16.05.2019 (SDG Leicester) '
             '\n Coded by: Martha M. Hoffmann '
             '\n Reiner Lemoine Institute (Berlin) \n \n ')

###############################################################################
# Get values from excel_template called in terminal                           #
# python3 A_main_script.py PATH/file.xlsx
###############################################################################

#os.system('clear')
#input_excel_file = str(sys.argv[1])
input_excel_file = './inputs/input_template_excel.xlsx'

#-------- Get all settings ---------------------------------------------------#
# General settings, general parameters, sensitivity parameters, project site  #
# data including timeseries (no noise, not clipped to evaluated timeframe     #
#-----------------------------------------------------------------------------#

from B_read_from_files import excel_template
settings, parameters_constant_values, parameters_sensitivity, project_site_s, case_definitions = \
    excel_template.settings(input_excel_file)

#---- Define all sensitivity_experiment_s, define result parameters ----------#
from C_sensitivity_experiments import generate_sensitvitiy_experiments, get_names
sensitivity_experiment_s, blackout_experiment_s, overall_results, names_sensitivities = \
    generate_sensitvitiy_experiments.get(settings, parameters_constant_values, parameters_sensitivity, project_site_s)

###############################################################################
# Process and initialize                                                      #
###############################################################################
#-------- Generate list of cases analysed in simulation ----------------------#
from D_process_input import process_input_parameters as process_input
case_list = process_input.list_of_cases(case_definitions)

logging.info('With these cases, a total of '+ str(settings['total_number_of_experiments'] * len(case_list)) + ' simulations will be performed. \n')

#----------------- Extend sensitivity_experiment_s----------------------------#
# with demand, pv_generation_per_kWp, wind_generation_per_kW                  #
#-----------------------------------------------------------------------------#
from D_process_input import noise, process_input_parameters
# Adapt timeseries of experiments according to evaluated days
max_date_time_index, max_evaluated_days = process_input_parameters.add_timeseries(sensitivity_experiment_s)
settings.update({'max_date_time_index': max_date_time_index})
settings.update({'max_evaluated_days': max_evaluated_days})

# -----------Apply noise to timeseries of each experiment --------------------#
# This results in unique timeseries for each experiment! For comparability    #
# it would be better to apply noise to each project site. However, if noise   #
# is subject to sensitivity analysis, this is not possible. To have the same  #
# noisy timeseries at a project site, noise has to be included in csv data!   #
#-----------------------------------------------------------------------------#
noise.apply(sensitivity_experiment_s)

# Calculation of grid_availability with randomized blackouts
from E_blackouts_central_grid import central_grid
if settings['necessity_for_blackout_timeseries_generation']==True:
    sensitivity_grid_availability, blackout_results = central_grid.get_blackouts(settings, blackout_experiment_s)

#---------------------------- Base case OEM ----------------------------------#
# Based on demand, pv generation and subjected to sensitivity analysis SOEM   #
#-----------------------------------------------------------------------------#
# import all scripts necessary for loop
from Z_general_functions import helpers
from F_case_definitions import cases
from G0_oemof_simulate import oemof_simulate

experiment_count = 0
total_number_of_simulations = settings['total_number_of_experiments'] * len(case_list)

for experiment in sensitivity_experiment_s:

    capacities_oem = {}

    if 'grid_availability' in sensitivity_experiment_s[experiment].keys():
        logging.debug('Using grid availability as included in timeseries file of project location.')
        # grid availability timeseries from file already included in data
    else:
        # extend experiment with blackout timeseries according to blackout parameters
        logging.debug('Using grid availability timeseries that was randomly generated.')
        blackout_experiment_name = get_names.blackout_experiment_name(sensitivity_experiment_s[experiment])
        sensitivity_experiment_s[experiment].update({'grid_availability':
                                                         sensitivity_grid_availability[blackout_experiment_name]})

    ###############################################################################
    # Simulations of all cases                                                    #
    # first the ones defining base capacities, then the others                    #
    ###############################################################################
    for specific_case in case_list:
        # --------get case definition for specific loop------------------------------#
        experiment_case_dict = \
            cases.update_dict(capacities_oem, case_definitions[specific_case], sensitivity_experiment_s[experiment])

        ###############################################################################
        # Creating, simulating and storing micro grid energy systems with oemof       #
        # According to parameters set beforehand                                      #
        ###############################################################################
        experiment_count = experiment_count + 1
        logging.info(
            'Starting simulation of case ' + specific_case + ', '
            + 'project site ' + sensitivity_experiment_s[experiment]['project_site_name'] + ', '
            + 'experiment no. ' + str(experiment_count) + '/'+ str(total_number_of_simulations) + '...')

        # Run simulation, evaluate results
        oemof_results = oemof_simulate.run(sensitivity_experiment_s[experiment], experiment_case_dict)

        # Extend base capacities for cases utilizing these values, only valid for specific experiment
        if case_definitions[specific_case]['based_on_case'] == False:
            capacities_oem.update({experiment_case_dict['case_name']: helpers.define_base_capacities(oemof_results)})

        # Extend oemof_results by blackout characteristics
        if 'grid_availability' in sensitivity_experiment_s[experiment].keys():
            blackout_result = central_grid.oemof_extension_for_blackouts(sensitivity_experiment_s[experiment]['grid_availability'])
            oemof_results   = central_grid.extend_oemof_results(oemof_results, blackout_result)
        else: # one might check for settings['necessity_for_blackout_timeseries_generation']==True here, but I think its unnecessary
            oemof_results   = central_grid.extend_oemof_results(oemof_results, blackout_results[blackout_experiment_name])

        # Extend overall results dataframe with simulation results
        overall_results = helpers.store_result_matrix(overall_results, sensitivity_experiment_s[experiment], oemof_results)
        # Writing DataFrame with all results to csv file
        overall_results.to_csv(sensitivity_experiment_s[experiment]['output_folder'] + '/' + sensitivity_experiment_s[experiment]['output_file'] + '.csv') # moved from below

        # Estimating simulation time left - more precise for greater number of simulations
        logging.info('    Estimated simulation time left: '
                     + str(round(sum(overall_results['evaluation_time'][:])
                                 * (total_number_of_simulations-experiment_count)/experiment_count/60,1))
                     + ' minutes.')
        print('\n')

    if settings['display_experiment'] == True:
        logging.info('The experiment with following parameters has been analysed:')
        pp.pprint(sensitivity_experiment_s[experiment])

# display all results
output_names = ['case']
output_names.extend(names_sensitivities)
output_names.extend(['lcoe', 'res_share'])
logging.info('\n Simulation complete. Resulting parameters saved in "results.csv". \n Overview over results:')
pp.pprint(overall_results[output_names])

logging.shutdown()

import shutil, os
path_from = os.path.abspath('./micro_grid_design_logfile.log')
path_to = os.path.abspath(settings['output_folder']+'/micro_grid_design_logfile.log')
shutil.move(path_from, path_to)