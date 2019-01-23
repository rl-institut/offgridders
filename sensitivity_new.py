'''
This script creates all possible experiments of a sensitivity analysis with a list of sensitive parameters
(bound by min, max, step lenght) and a list of constant parameters. All parameters are stored in a large
dictonary, including filenames.
'''

import pandas as pd
import logging
from read_from_files import excel_template
import itertools
import numpy as np
import pprint as pp

class experiment_dict:

    def get():
        settings, parameters_constant_values, parameters_sensitivity, project_sites, case_definitions = excel_template.settings()

        if settings['sensitivity_all_combinations'] == True:
            sensitivity_experiments, number_of_project_sites, sensitivity_array_dict, number_of_project_sites = \
                experiment_dict.combinations_all_possible(settings, parameters_constant_values, parameters_sensitivity, project_sites)

        elif settings['sensitivity_all_combinations'] == False:
            sensitivity_experiments, number_of_project_sites, sensitivity_array_dict, number_of_project_sites = \
                experiment_dict.combinations_with_base_case(settings, parameters_constant_values, parameters_sensitivity, project_sites)

        else:
            logging.warning('Setting "sensitivity_all_combinations" not valid! Has to be TRUE or FALSE.')

        experiments, total_number_of_experiments = get.project_site_experiments(sensitivity_experiments, project_sites)

        for experiment_number in experiments:
            get.experiment_name(experiments[experiment_number], sensitivity_array_dict,
                            number_of_project_sites)

        title_overall_results = get.overall_results_title(number_of_project_sites, sensitivity_array_dict)

        experiments_dataframe = pd.DataFrame.from_dict(sensitivity_experiments, orient='index')
        experiments_dataframe.to_csv(settings['output_folder']+'/Input_data_of_all_cases.csv')

        message = 'For ' + str(number_of_project_sites)
        message += ' with ' + str(int(total_number_of_experiments/number_of_project_sites)) + ' scenarios each'
        message += ' a total of ' + str(total_number_of_experiments) + ' experiments will be performed'

        logging.info(message)
        print(message)

        return experiments, title_overall_results

    def combinations_all_possible(settings, parameters_constant_values, parameters_sensitivity, project_sites):

        remove_doubles.constants_senstivity(parameters_constant_values, parameters_sensitivity)

        # From now on, universal parameters poses the base scenario. some parameters might only be set with project sites!
        universal_parameters, number_of_project_sites = get.universal_parameters(settings, parameters_constant_values, parameters_sensitivity,
                                                        project_sites)

        sensitivity_array_dict = get.dict_sensitivies_arrays(parameters_sensitivity, project_sites)

        sensitivity_experiments = get.all_combinations(sensitivity_array_dict, project_sites, number_of_project_sites)

        for experiment_number in sensitivity_experiments:
            sensitivity_experiments[experiment_number].update(universal_parameters.copy())

        return sensitivity_experiments, number_of_project_sites, sensitivity_array_dict, number_of_project_sites

    def combinations_with_base_case(settings, parameters_constant_values, parameters_sensitivity, project_sites):
        universal_parameters, number_of_project_sites = get.universal_parameters(settings, parameters_constant_values, parameters_sensitivity,
                                                        project_sites)

        # From now on, universal parameters poses the base scenario. some parameters might only be set with project sites!
        sensitivity_array_dict = get.dict_sensitivies_arrays(parameters_sensitivity, project_sites)

        experiment_number = 1
        sensitivity_experiments = {1: universal_parameters.copy()}

        for key in sensitivity_array_dict:
            for interval_entry in range(0, len(sensitivity_array_dict[key])):
                if sensitivity_array_dict[key][interval_entry] != universal_parameters[key]:
                    experiment_number = experiment_number + 1
                    # As long as key not in universal parameters (base case) create new experiment
                    # All parameters like base case except for sensitivity parameter
                    sensitivity_experiments.update({experiment_number: universal_parameters.copy()})
                    sensitivity_experiments[experiment_number].update({key: sensitivity_array_dict[key][interval_entry]})

        return sensitivity_experiments, number_of_project_sites, sensitivity_array_dict, number_of_project_sites

class get:
    def universal_parameters(settings, parameters_constant_values, parameters_sensitivity, project_sites):

        remove_doubles.constants_project_sites(parameters_constant_values, project_sites)
        remove_doubles.project_sites_sensitivity(parameters_sensitivity, project_sites)

        # create base case
        universal_parameters = settings.copy()
        universal_parameters.update(parameters_constant_values.copy())

        number_of_project_sites = 0
        for key in project_sites:
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

    def all_combinations(sensitivity_array_dict, project_sites, number_of_project_sites):
        # create all possible combinations of sensitive parameters
        keys, values = zip(*sensitivity_array_dict.items())
        all_experiments = [dict(zip(keys, v)) for v in itertools.product(*values)]

        number_of_experiment = 0
        sensitivity_experiments = {}
        for experiment in all_experiments:
            number_of_experiment += 1
            sensitivity_experiments.update({number_of_experiment: experiment.copy()})

        return sensitivity_experiments

    def experiment_name(experiment, sensitivity_array_dict, number_of_project_sites):
        # define file postfix to save simulation
         # todo some kind of sorting         sensitivity_array_ = pd.DataFrame.from_dict(sensitivity_array_dict, orient='index').sort_index(axis='index')
        filename = '_s'
        if number_of_project_sites > 1:
            if isinstance(experiment['project_site_name'], str):
                filename = filename + '_' + experiment['project_site_name']
            else:
                filename = filename + '_' + str(experiment['project_site_name'])
        else:
            filename = filename

        for keys in sensitivity_array_dict:
            if isinstance(experiment[keys], str):
                filename = filename + '_' + keys + '_' + experiment[keys]
            else:
                filename = filename + '_' + keys + '_' + str(round(experiment[keys],2))
        if filename == '_s':
            filename = ''
        experiment.update({'filename': filename})
        return

    def project_site_experiments(sensitivity_experiments, project_sites):
        experiments = {}
        number_of_experiments = 0
        for experiment in sensitivity_experiments:
            for key in project_sites:
                # fill dictionary with all constant values defining the different simulations of the sensitivity analysis
                # ! do not use a key two times or in sensitivity_bounds as well, as it will be overwritten by new information
                number_of_experiments += 1
                experiments.update({number_of_experiments: sensitivity_experiments[experiment].copy()})
                experiments[number_of_experiments].update({'project_site_name': key})
                experiments[number_of_experiments].update(project_sites[key].copy())

        return experiments, number_of_experiments

    def overall_results_title(number_of_project_sites, sensitivity_array_dict):
        # Get from config which results are to be included in csv
        from config import results_demand_characteristics, results_blackout_characteristics, results_annuities, \
            results_costs
        title_overall_results = pd.DataFrame(columns=[
            'case',
            'filename'])

        if results_demand_characteristics == True:
            title_overall_results = pd.concat([title_overall_results, pd.DataFrame(columns=[
                'total_demand_annual_kWh',
                'demand_peak_kW',
                'total_demand_supplied_annual_kWh',
                'total_demand_shortage_annual_kWh'])], axis=1, sort=False)

        if results_blackout_characteristics == True:
            title_overall_results = pd.concat([title_overall_results, pd.DataFrame(columns=[
                'national_grid_reliability',
                'national_grid_total_blackout_duration',
                'national_grid_number_of_blackouts'])], axis=1, sort=False)

        title_overall_results = pd.concat([title_overall_results, pd.DataFrame(columns=[
            'capacity_pv_kWp',
            'capacity_storage_kWh',
            'capacity_genset_kW',
            'capacity_pcoupling_kW',
            'res_share',
            'consumption_fuel_annual_l',
            'consumption_main_grid_mg_side_annual_kWh',
            'feedin_main_grid_mg_side_annual_kWh'])], axis=1, sort=False)

        if results_annuities == True:
            title_overall_results = pd.concat([title_overall_results, pd.DataFrame(columns=[
                'annuity_pv',
                'annuity_storage',
                'annuity_genset',
                'annuity_pcoupling',
                'annuity_distribution_grid',
                'annuity_project',
                'annuity_grid_extension'])], axis=1, sort=False)

        title_overall_results = pd.concat([title_overall_results, pd.DataFrame(columns=[
            'expenditures_fuel_annual',
            'expenditures_main_grid_consumption_annual',
            'revenue_main_grid_feedin_annual'])], axis=1, sort=False)

        # Called costs because they include the operation, while they are also not the present value because
        # the variable costs are included in the oem
        if results_costs == True:
            title_overall_results = pd.concat([title_overall_results, pd.DataFrame(columns=[
                'costs_pv',
                'costs_storage',
                'costs_genset',
                'costs_pcoupling',
                'costs_distribution_grid',
                'costs_project',
                'costs_grid_extension',
                'expenditures_fuel_total',
                'expenditures_main_grid_consumption_total',
                'revenue_main_grid_feedin_total'])], axis=1, sort=False)

        title_overall_results = pd.concat([title_overall_results, pd.DataFrame(columns=[
            'annuity',
            'npv',
            'lcoe',
            'supply_reliability',
            'objective_value',
            'simulation_time',
            'comments'])], axis=1, sort=False)

        if number_of_project_sites > 1:
            title_overall_results = pd.concat([title_overall_results, pd.DataFrame(columns=['project_site_name'])], axis=1)

        for keys in sensitivity_array_dict:
            title_overall_results = pd.concat([title_overall_results, pd.DataFrame(columns=[keys])], axis=1)

        return title_overall_results


class remove_doubles():
    def constants_project_sites(parameters_constant_values, project_sites):
        # todo test and describe
        # remove all entries that are doubled in parameters_constant_values, settings & project_sites from parameters_constant_values
        str = 'Attributes "'
        keys = parameters_constant_values.copy().keys()
        for key in keys:
            if key in project_sites:
                del parameters_constant_values[key]
                str += key + ", "
        if str != 'Attributes "':
            str = str[
                  :-2] + '" defined in constant and project site parameters. Only project site value will be used for experiments.'
            logging.warning(str)
        return

    def project_sites_sensitivity(parameters_sensitivity, project_sites):
        # todo test and describe
        # remove all entries that are doubled in sensitivity_bounds, project_sites
        str = 'Attributes "'
        keys = parameters_sensitivity.copy().keys()
        for key in keys:
            if key in project_sites:
                #todo this preferrs project site definition over sensitivity definition
                # todo base case definition not based on individual project sites if sensitivity performed, instead based on constant values. meaning, eventhough for villA fuel=2 and villB fuel=3, in const fuel = 1, each has base case with const fuel = 1
                del parameters_sensitivity[key]
                str += key + ", "
        if str != 'Attributes "':
            str = str[
                  :-2] + '" defined in project site and sensitvity parameters. Only sensitivity parameters will be used for experiments.'
            logging.warning(str)
        return

    def constants_senstivity(parameters_constant_values, parameters_sensitivity):
        # todo test and describe
        # remove all entries that are doubled in parameters_constant_values, settings & parameters_sensitivity
        str = 'Attributes "'
        keys = parameters_constant_values.copy().keys()
        for key in keys:
            if key in parameters_sensitivity:
                del parameters_constant_values[key]
                str += key + ", "
        if str != 'Attributes "':
            str = str[
                  :-2] + '" defined in constant and sensitivity parameters. Only sensitivity parameter value will be used for experiments.'
            logging.warning(str)
        return


class sensitivity():

    def blackout_experiments():
        from input_values import sensitivity_bounds, sensitivity_constants
        import itertools
        import numpy as np

        dictof_blackoutparameters = {}
        for keys in sensitivity_bounds:
            if keys == 'blackout_duration' or keys == 'blackout_frequency' or keys == 'blackout_duration_std_deviation' or keys == 'blackout_frequency_std_deviation':
                if sensitivity_bounds[keys]['min'] == sensitivity_bounds[keys]['max']:
                    dictof_blackoutparameters.update({keys: np.array([sensitivity_bounds[keys]['min']])})
                else:
                    dictof_blackoutparameters.update({keys: np.arange(sensitivity_bounds[keys]['min'],
                                                                 sensitivity_bounds[keys]['max']+sensitivity_bounds[keys]['step']/2,
                                                                 sensitivity_bounds[keys]['step'])})
        for keys in sensitivity_constants:
            if keys == 'blackout_duration' or keys == 'blackout_frequency' or keys == 'blackout_duration_std_deviation' or keys == 'blackout_frequency_std_deviation':
                dictof_blackoutparameters.update({keys: np.array([sensitivity_constants[keys]])})

        # create all possible combinations of sensitive parameters
        keys, values = zip(*dictof_blackoutparameters.items())
        blackout_experiments = [dict(zip(keys, v)) for v in itertools.product(*values)]
        # define file name to save simulation / get grid availabilities
        for i in range(0, len(blackout_experiments)):
            blackout_experiment_name = sensitivity.blackout_experiment_name(blackout_experiments[i])
            blackout_experiments[i].update({'experiment_name': blackout_experiment_name})
        return blackout_experiments

    # Generate names for blackout experiments, used in sensitivity.blackoutexperiments and in maintool
    def blackout_experiment_name(blackout_experiment):
        blackout_experiment_name = 'blackout_dur' + '_' + str(round(blackout_experiment['blackout_duration'], 2)) + "_" \
                          + 'dur_dev' + '_' + str(round(blackout_experiment['blackout_duration_std_deviation'], 2)) + "_" \
                          + 'freq' + '_' + str(round(blackout_experiment['blackout_frequency'], 2)) + "_" \
                          + 'freq_dev' + '_' + str(round(blackout_experiment['blackout_frequency_std_deviation'], 2))
        return blackout_experiment_name

experiment_dict.get()