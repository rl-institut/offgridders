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
sensitivity_experiment_s, blackout_experiment_s, overall_results = generate_sensitvitiy_experiments.get(settings, parameters_constant_values, parameters_sensitivity, project_site_s)

###############################################################################
# Process and initialize        #
###############################################################################
#-------- Check for, create or empty results directory -----------------------#
from Z_output_functions import output
output.check_output_directory(sensitivity_experiment_s) # todo too many times folders generated and/or deleted

#-------- Generate list of cases analysed in simulation ----------------------#
# missing process input: date time frame -> does it make more sense to keep settings konstant and give to each function or increase disc volume by having it for EACH EXPERIMENT?
from D_process_input import process_input_parameters as process_input
case_list = process_input.list_of_cases(case_definitions)
# todo shortage at no shortage!!
#----------------- Extend sensitivity_experiment_s----------------------------#
# with demand, pv_generation_per_kWp, wind_generation_per_kW                  #
#-----------------------------------------------------------------------------#
from D_process_input import noise, process_input_parameters
# adapt timestamp for timeseries
max_date_time_index, max_evaluated_days = process_input_parameters.add_timeseries(sensitivity_experiment_s)
settings.update({'date_time_index': max_date_time_index})
settings.update({'evaluated_days': max_evaluated_days})

# Apply noise
noise.apply(sensitivity_experiment_s)

# Calculation of grid_availability with randomized blackouts
from E_blackouts_central_grid import central_grid
sensitivity_grid_availability, blackout_results = central_grid.get_blackouts(settings, blackout_experiment_s)

#---------------------------- Base case OEM ----------------------------------#
# Based on demand, pv generation and subjected to sensitivity analysis SOEM   #
#-----------------------------------------------------------------------------#
# import all scripts necessary for loop
from Z_general_functions import helpers
from F_case_definitions import cases
from G0_oemof_simulate import oemof_simulate

# todo show figures but continue script!
experiment_count = 0
capacities_oem = {}

for experiment in sensitivity_experiment_s:

    experiment_count = experiment_count + 1


    blackout_experiment_name = get_names.blackout_experiment_name(sensitivity_experiment_s[experiment])
    sensitivity_experiment_s[experiment].update({'grid_availability': sensitivity_grid_availability[blackout_experiment_name]})
    ###############################################################################
    # Simulations of all cases                                                    #
    # first the ones defining base capacities, then the others                    #
    ###############################################################################
    for specific_case in case_list:
        # get case definition
        experiment_case_dict = cases.update_dict(capacities_oem, case_definitions[specific_case], sensitivity_experiment_s[experiment])
        ###############################################################################
        # Creating, simulating and storing micro grid energy systems with oemof
        # According to parameters set beforehand
        ###############################################################################
        logging.info(
            'Starting simulation of case ' + specific_case + ', experiment no. ' + str(experiment_count) + '...')

        oemof_results = oemof_simulate.run(sensitivity_experiment_s[experiment], experiment_case_dict)

        if case_definitions[specific_case]['based_on_case'] == False:
            capacities_oem.update({experiment_case_dict['case_name']: helpers.define_base_capacities(oemof_results)})
        #todo off-grid right now COMPLETELY failing storage capacity compilation - why?!
        # Extend oemof_results by blackout characteristics
        oemof_results   = central_grid.extend_oemof_results(oemof_results, blackout_results[blackout_experiment_name])
        # Extend overall results dataframe with simulation results
        overall_results = helpers.store_result_matrix(overall_results, sensitivity_experiment_s[experiment], oemof_results)

    if settings['print_simulation_experiment'] == True:
        logging.info('The experiment with following parameters has been analysed:')
        pp.pprint(sensitivity_experiment_s[experiment])

    # Writing DataFrame with all results to csv file
    overall_results.to_csv(sensitivity_experiment_s[experiment]['output_folder'] + '/results.csv')

# display all results
pp.pprint(overall_results)
###############################################################################
# Plot all graphs
###############################################################################