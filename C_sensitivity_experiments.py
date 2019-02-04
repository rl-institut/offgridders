'''
This script creates all possible sensitivity_experiment_s of a sensitivity analysis with a list of sensitive parameters
(bound by min, max, step lenght) and a list of constant parameters. All parameters are stored in a large
dictonary, including filenames.
'''

import pandas as pd
import logging

import itertools
import numpy as np
import pprint as pp
from D_process_input import process_input_parameters as process_input
from Z_output_functions import output_results

class generate_sensitvitiy_experiments:
    def get(settings, parameters_constant_values, parameters_sensitivity, project_sites):
        #######################################################
        # Get sensitivity_experiment_s for sensitivity analysis            #
        #######################################################
        if settings['sensitivity_all_combinations'] == True:
            sensitivitiy_experiments_s, number_of_project_sites, sensitivity_array_dict, total_number_of_experiments = \
                generate_experiments.all_possible(settings, parameters_constant_values, parameters_sensitivity, project_sites)

        elif settings['sensitivity_all_combinations'] == False:
            sensitivitiy_experiments_s, number_of_project_sites, sensitivity_array_dict, total_number_of_experiments = \
                generate_experiments.with_base_case(settings, parameters_constant_values, parameters_sensitivity, project_sites)

        else:
            logging.warning('Setting "sensitivity_all_combinations" not valid! Has to be TRUE or FALSE.')
        for experiment in sensitivitiy_experiments_s:
            #  Add economic values to sensitivity sensitivity_experiment_s
            process_input.economic_values(sensitivitiy_experiments_s[experiment])
            # Give a file name to the sensitivity_experiment_s
            get_names.experiment_name(sensitivitiy_experiments_s[experiment], sensitivity_array_dict,
                                number_of_project_sites)
            if sensitivitiy_experiments_s[experiment]['storage_initial_soc']=='None':
                sensitivitiy_experiments_s[experiment].update({'storage_initial_soc': None})
        #######################################################
        # Get blackout_experiment_s for sensitvitiy           #
        #######################################################
        # Creating duict of possible blackout scenarios (combinations of durations  frequencies
        blackout_experiment_s, blackout_experiments_count \
            = generate_experiments.blackout(sensitivity_array_dict, parameters_constant_values, settings)

        # save all Experiments with all used input data to csv (not really necessary)
        experiments_dataframe = pd.DataFrame.from_dict(sensitivitiy_experiments_s, orient='index')
        experiments_dataframe.to_csv(settings['output_folder']+'/Input_data_of_all_cases.csv')

        # Generate a overall title of the oemof-results DataFrame
        title_overall_results = output_results.overall_results_title(settings, number_of_project_sites, sensitivity_array_dict)

        message = 'For ' + str(number_of_project_sites) + ' project sites'
        message += ' with ' + str(int(total_number_of_experiments/number_of_project_sites)) + ' scenarios each'
        message += ' a total of ' + str(total_number_of_experiments) + ' sensitivity_experiment_s will be performed for each case.'

        logging.info(message)
        return sensitivitiy_experiments_s, blackout_experiment_s, title_overall_results

class generate_experiments():
    def all_possible(settings, parameters_constant_values, parameters_sensitivity, project_sites):

        remove_doubles.constants_senstivity(parameters_constant_values, parameters_sensitivity)

        # From now on, universal parameters poses the base scenario. some parameters might only be set with project sites!
        universal_parameters, number_of_project_sites = get.universal_parameters(settings, parameters_constant_values, parameters_sensitivity,
                                                        project_sites)

        sensitivity_array_dict = get.dict_sensitivies_arrays(parameters_sensitivity, project_sites)

        project_site_dict = {'project_site_name': [key for key in project_sites.keys()]}
        sensitivity_experiments, total_number_of_experiments = get.all_possible_combinations(sensitivity_array_dict, project_site_dict)

        for experiment in sensitivity_experiments:
            sensitivity_experiments[experiment].update(universal_parameters.copy())
            sensitivity_experiments[experiment].update(project_sites[sensitivity_experiments[experiment]['project_site_name']].copy())

        return sensitivity_experiments, number_of_project_sites, sensitivity_array_dict, total_number_of_experiments

    def with_base_case(settings, parameters_constant_values, parameters_sensitivity, project_sites):
        universal_parameters, number_of_project_sites = get.universal_parameters(settings, parameters_constant_values, parameters_sensitivity,
                                                        project_sites)

        # From now on, universal parameters poses the base scenario. some parameters might only be set with project sites!
        sensitivity_array_dict = get.dict_sensitivies_arrays(parameters_sensitivity, project_sites)

        sensitivity_experiments, total_number_of_experiments = get.combinations_around_base(sensitivity_array_dict, universal_parameters, project_sites)

        return sensitivity_experiments, number_of_project_sites, sensitivity_array_dict, total_number_of_experiments

    def blackout(sensitivity_array_dict, parameters_constants, settings):
        blackout_parameters = sensitivity_array_dict.copy()
        for parameter in sensitivity_array_dict:
            if parameter != 'blackout_duration' and parameter != 'blackout_frequency' and parameter != 'blackout_duration_std_deviation' and parameter != 'blackout_frequency_std_deviation':
                del blackout_parameters[parameter]

        blackout_constants = parameters_constants.copy()
        for parameter in parameters_constants:
            if parameter != 'blackout_duration' and parameter != 'blackout_frequency' and parameter != 'blackout_duration_std_deviation' and parameter != 'blackout_frequency_std_deviation':
                del blackout_constants[parameter]

        if settings['sensitivity_all_combinations'] == True:
            blackout_experiment_s = get.all_possible_combinations(blackout_parameters, {})
            for blackout_experiment in blackout_experiment_s:
                blackout_experiment_s[blackout_experiment].update(blackout_constants.copy())

        elif settings['sensitivity_all_combinations'] == False:
            blackout_experiment_s = {}
            blackout_experiments_count = 0
            defined_base = False
            for key in blackout_parameters:
                for interval_entry in range(0, len(sensitivity_array_dict[key])):
                    if key in blackout_constants:
                        key_value = blackout_constants[key]
                    else:
                        # if not defined in project sites or universal values, use sensitivity value
                        key_value = None

                    if sensitivity_array_dict[key][interval_entry] != key_value:
                        # All parameters like base case except for sensitivity parameter
                        blackout_experiments_count += 1
                        blackout_experiment_s.update({blackout_experiments_count: blackout_constants.copy()})
                        blackout_experiment_s[blackout_experiments_count].update({key: sensitivity_array_dict[key][interval_entry]})
                    elif sensitivity_array_dict[key][interval_entry] == key_value and defined_base == False:
                        # Defining scenario only with base case values for universal parameter / specific to project site (once!)
                        blackout_experiments_count += 1
                        blackout_experiment_s.update({blackout_experiments_count: blackout_constants.copy()})
                        blackout_experiment_s[blackout_experiments_count].update({key: key_value})
                        defined_base == True
            if len(blackout_experiment_s)==0:
                blackout_experiments_count += 1
                blackout_experiment_s.update({blackout_experiments_count: blackout_constants.copy()})

        else:
            logging.warning('Setting "sensitivity_all_combinations" not valid! Has to be TRUE or FALSE.')

        # define file name to save simulation / get grid availabilities
        for blackout_experiment in blackout_experiment_s:
            blackout_experiment_name = get_names.blackout_experiment_name(blackout_experiment_s[blackout_experiment])
            blackout_experiment_s[blackout_experiment].update({'experiment_name': blackout_experiment_name})

        logging.info(
            str(len(blackout_experiment_s)) + ' combinations of blackout duration and frequency will be analysed.')

        return blackout_experiment_s, blackout_experiments_count

class get:
    def universal_parameters(settings, parameters_constant_values, parameters_sensitivity, project_site_s):
        remove_doubles.constants_project_sites(parameters_constant_values, project_site_s)
        remove_doubles.project_sites_sensitivity(parameters_sensitivity, project_site_s)

        # create base case
        universal_parameters = settings.copy()
        universal_parameters.update(parameters_constant_values.copy())

        number_of_project_sites = 0
        for key in project_site_s:
            number_of_project_sites += 1

        return universal_parameters, number_of_project_sites

    def dict_sensitivies_arrays(parameters_sensitivity, project_sites):
        # fill dictionary with all sensitivity ranges defining the different simulations of the sensitivity analysis
        # ! do not use a key two times, as it will be overwritten by new information
        sensitivity_array_dict = {}
        for keys in parameters_sensitivity:
            if parameters_sensitivity[keys]['Min'] == parameters_sensitivity[keys]['Max']:
                sensitivity_array_dict.update({keys: np.array([parameters_sensitivity[keys]['Min']])})
            else:
                sensitivity_array_dict.update({keys: np.arange(parameters_sensitivity[keys]['Min'],
                                                                parameters_sensitivity[keys]['Max']+parameters_sensitivity[keys]['Step']/2,
                                                                parameters_sensitivity[keys]['Step'])})
        return sensitivity_array_dict

    def all_possible_combinations(sensitivity_array_dict, name_entry_dict):
        # create all possible combinations of sensitive parameters
        generate_sensitvitiy_experiments.update(name_entry_dict)
        keys, values = zip(*sensitivity_array_dict.items())
        all_experiments = [dict(zip(keys, v)) for v in itertools.product(*values)]

        number_of_experiment = 0
        sensitivity_experiment_s = {}
        for experiment in all_experiments:
            number_of_experiment += 1
            sensitivity_experiment_s.update({number_of_experiment: experiment.copy()})

        total_number_of_experiments = number_of_experiment
        return sensitivity_experiment_s, total_number_of_experiments

    def combinations_around_base(sensitivity_array_dict, universal_parameters, project_site_s):

        experiment_number = 0
        sensitivity_experiment_s = {}

        for project_site in project_site_s:
            # if no sensitivity analysis performed (other than multiple locations)
            if len(sensitivity_array_dict.keys()) == 0:
                experiment_number += 1
                sensitivity_experiment_s.update({experiment_number: universal_parameters.copy()})
                sensitivity_experiment_s[experiment_number].update({'project_site_name': project_site})
                sensitivity_experiment_s[experiment_number].update(project_site_s[project_site].copy())
            # generate cases with sensitivity parameters
            else:
                defined_base = False

                for key in sensitivity_array_dict:
                    for interval_entry in range(0, len(sensitivity_array_dict[key])):
                        if key in project_site_s[project_site]:
                            # if defined in project sites, use this value as base case value
                            key_value = project_site_s[project_site][key]
                        elif key in universal_parameters:
                            # if not defined in project sites, use this value as base case value
                            key_value = universal_parameters[key]
                        else:
                            # if not defined in project sites or universal values, use sensitivity value
                            key_value = None

                        if sensitivity_array_dict[key][interval_entry] != key_value:
                            # All parameters like base case except for sensitivity parameter
                            experiment_number += 1
                            sensitivity_experiment_s.update({experiment_number: universal_parameters.copy()})
                            sensitivity_experiment_s[experiment_number].update({key: sensitivity_array_dict[key][interval_entry]})
                            sensitivity_experiment_s[experiment_number].update({'project_site_name': project_site})
                            sensitivity_experiment_s[experiment_number].update(project_site_s[project_site].copy())
                            # scaling demand according to scaling factor - used for tests regarding tool application
                            sensitivity_experiment_s[experiment_number].update({'demand': sensitivity_experiment_s[experiment_number]['demand'] * sensitivity_experiment_s[experiment_number]['demand_scaling_factor']})

                        elif sensitivity_array_dict[key][interval_entry] == key_value and defined_base == False:
                            # Defining scenario only with base case values for universal parameter / specific to project site (once!)
                            experiment_number += 1
                            sensitivity_experiment_s.update({experiment_number: universal_parameters.copy()})
                            sensitivity_experiment_s[experiment_number].update({key: key_value})
                            sensitivity_experiment_s[experiment_number].update({'project_site_name': project_site})
                            sensitivity_experiment_s[experiment_number].update(project_site_s[project_site].copy())
                            # scaling demand according to scaling factor - used for tests regarding tool application
                            sensitivity_experiment_s[experiment_number].update({'demand': sensitivity_experiment_s[experiment_number]['demand'] * sensitivity_experiment_s[experiment_number]['demand_scaling_factor']})
                            defined_base == True



        total_number_of_experiments = experiment_number
        return sensitivity_experiment_s, total_number_of_experiments

    def project_site_experiments(sensitivity_experiment_s, project_sites):
        experiment_s = {}
        number_of_experiments = 0
        for experiment in sensitivity_experiment_s:
                # fill dictionary with all constant values defining the different simulations of the sensitivity analysis
                # ! do not use a key two times or in sensitivity_bounds as well, as it will be overwritten by new information
            number_of_experiments += 1
            experiment_s.update({number_of_experiments: sensitivity_experiment_s[experiment].copy()})
            experiment_s[number_of_experiments].update(project_sites[experiment_s[experiment]['project_site_name']].copy())

        return experiment_s, number_of_experiments


class get_names():
    def experiment_name(experiment, sensitivity_array_dict, number_of_project_sites):
        # define file postfix to save simulation
        filename = '_s'
        if number_of_project_sites > 1:
            if isinstance(experiment['project_site_name'], str):
                filename = filename + '_' + experiment['project_site_name']
            else:
                filename = filename + '_' + str(experiment['project_site_name'])
        else:
            filename = filename

        # this generates alphabetically sorted file/experiment titles
        # ensuring that simulations can be restarted and old results are recognized
        sensitivity_titles = pd.DataFrame.from_dict(sensitivity_array_dict, orient='index').sort_index().index
        #generating all names
        for keys in sensitivity_titles:
            if isinstance(experiment[keys], str):
                filename = filename + '_' + keys + '_' + experiment[keys]
            else:
                filename = filename + '_' + keys + '_' + str(round(experiment[keys], 2))
        # is no sensitivity analysis performed, do not add filename
        if filename == '_s':
            filename = ''
        experiment.update({'filename': filename})
        return

    # Generate names for blackout sensitivity_experiment_s, used in sensitivity.blackoutexperiments and in maintool
    def blackout_experiment_name(blackout_experiment):
        blackout_experiment_name = 'blackout_dur' + '_' + str(round(blackout_experiment['blackout_duration'], 2)) + "_" \
                                   + 'dur_dev' + '_' + str(
            round(blackout_experiment['blackout_duration_std_deviation'], 2)) + "_" \
                                   + 'freq' + '_' + str(round(blackout_experiment['blackout_frequency'], 2)) + "_" \
                                   + 'freq_dev' + '_' + str(
            round(blackout_experiment['blackout_frequency_std_deviation'], 2))
        return blackout_experiment_name


class remove_doubles():
    def constants_project_sites(parameters_constant_values, project_sites):
        # remove all entries that are doubled in parameters_constant_values, settings & project_site_s from parameters_constant_values
        str = 'Attributes "'
        keys = parameters_constant_values.copy().keys()
        for key in keys:
            if key in project_sites:
                del parameters_constant_values[key]
                str += key + ", "
        if str != 'Attributes "':
            str = str[
                  :-2] + '" defined in constant and project site parameters. Only project site value will be used for sensitivity_experiment_s.'
            logging.warning(str)
        return

    def project_sites_sensitivity(parameters_sensitivity, project_sites):
        # remove all entries that are doubled in sensitivity_bounds, project_site_s
        str = 'Attributes "'
        keys = parameters_sensitivity.copy().keys()
        for key in keys:
            if key in project_sites:
                # ?? this preferrs project site definition over sensitivity definition
                # ?? base case definition not based on individual project sites if sensitivity performed, instead based on constant values. meaning, eventhough for villA fuel=2 and villB fuel=3, in const fuel = 1, each has base case with const fuel = 1
                del parameters_sensitivity[key]
                str += key + ", "
        if str != 'Attributes "':
            str = str[
                  :-2] + '" defined in project site and sensitvity parameters. Only sensitivity parameters will be used for sensitivity_experiment_s.'
            logging.warning(str)
        return

    def constants_senstivity(parameters_constant_values, parameters_sensitivity):
        # remove all entries that are doubled in parameters_constant_values, settings & parameters_sensitivity
        str = 'Attributes "'
        keys = parameters_constant_values.copy().keys()
        for key in keys:
            if key in parameters_sensitivity:
                del parameters_constant_values[key]
                str += key + ", "
        if str != 'Attributes "':
            str = str[
                  :-2] + '" defined in constant and sensitivity parameters. Only sensitivity parameter value will be used for sensitivity_experiment_s.'
            logging.warning(str)
        return
