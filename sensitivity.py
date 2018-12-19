'''
This script creates all possible experiments of a sensitivity analysis with a list of sensitive parameters
(bound by min, max, step lenght) and a list of constant parameters. All parameters are stored in a large
dictonary, including filenames.
'''

import pandas as pd
import logging

class sensitivity():
    def experiments():
        from input_values import input_files_demand, sensitivity_bounds, sensitivity_constants
        import itertools
        import numpy as np
        # create empty dictionary
        dictof_oemparameters = {}

        # check for parameters defined twice in input_values_py
        for keys in sensitivity_constants:
            if sensitivity_bounds.get(keys):
                logging.warning("Key " + keys + " was used in sensitivity bounds as well as in sensitivity constants!"
                                + "\n         The constant value will be used for proceeding simulations.")

        # fill dictionary with all sensitivity ranges defining the different simulations of the sensitivity analysis
        # ! do not use a key two times, as it will be overwritten by new information
        for keys in sensitivity_bounds:
            if sensitivity_bounds[keys]['min'] == sensitivity_bounds[keys]['max']:
                dictof_oemparameters.update({keys: np.array([sensitivity_bounds[keys]['min']])})
            else:
                dictof_oemparameters.update({keys: np.arange(sensitivity_bounds[keys]['min'],
                                                             sensitivity_bounds[keys]['max']+sensitivity_bounds[keys]['step']/2,
                                                             sensitivity_bounds[keys]['step'])})
        # fill dictionary with all constant values defining the different simulations of the sensitivity analysis
        # ! do not use a key two times or in sensitivity_bounds as well, as it will be overwritten by new information
        for keys in sensitivity_constants:
            dictof_oemparameters.update({keys: np.array([sensitivity_constants[keys]])})

        demand_array = []
        for files in input_files_demand:
            demand_array.append(files)

        dictof_oemparameters.update({'demand_profile': demand_array})

        # create all possible combinations of sensitive parameters
        keys, values = zip(*dictof_oemparameters.items())
        experiments = [dict(zip(keys, v)) for v in itertools.product(*values)]

        # define file postfix to save simulation
        for i in range(0, len(experiments)):
            filename = '_s'
            if len(demand_array) > 1:
                filename = filename + '_' + experiments[i]['demand_profile']
            else:
                filename = filename
            for keys in sensitivity_bounds:
            #for keys in experiments[i]:
                filename = filename + '_' + keys + '_' + str(round(experiments[i][keys],2))
            if filename == '_s':
                filename = ''
            experiments[i].update({'filename': filename})

        # define structure of pd.Dataframe: overall_results
        # todo more automatic extension of colum header
        # todo: add 'grid_reliability', 'grid_total_blackout_duration', 'grid_number_of_blackouts'

        overall_results = sensitivity.overall_results_title(len(demand_array), sensitivity_bounds)

        return experiments, overall_results

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

    # please add additional arguments here.
    def overall_results_title(number_of_demand_profiles, sensitivity_bounds):
        # Get from config which results are to be included in csv
        from config import results_demand_characteristics, results_blackout_characteristics, results_annuities, results_costs
        overall_results = pd.DataFrame(columns=[
            'case',
            'filename'])

        if results_demand_characteristics == True:
            overall_results = pd.concat([overall_results, pd.DataFrame(columns=[
                'total_demand_annual_kWh',
                'demand_peak_kW',
                'demand_annual_supplied_kWh'])], axis=1, sort=False)

        if results_blackout_characteristics == True:
            overall_results = pd.concat([overall_results, pd.DataFrame(columns=[
                'national_grid_reliability',
                'national_grid_total_blackout_duration',
                'national_grid_number_of_blackouts'])], axis=1, sort=False)

        overall_results = pd.concat([overall_results, pd.DataFrame(columns=[
            'capacity_pv_kWp',
            'capacity_storage_kWh',
            'capacity_genset_kW',
            'capacity_pcoupling_kW',
            'res_share',
            'consumption_fuel_annual_l',
            'consumption_main_grid_annual_kWh',
            'feedin_main_grid_annual_kWh'])], axis=1, sort=False)

        if results_annuities == True:
            overall_results = pd.concat([overall_results, pd.DataFrame(columns=[
                'annuity_pv',
                'annuity_storage',
                'annuity_genset',
                'annuity_pcoupling',
                'annuity_distribution_grid',
                'annuity_project',
                'annuity_grid_extension'])], axis=1, sort=False)

        overall_results = pd.concat([overall_results, pd.DataFrame(columns=[
            'expenditures_fuel_annual',
            'expenditures_main_grid_consumption_annual',
            'revenue_main_grid_feedin_annual'])], axis=1, sort=False)

        # Called costs because they include the operation, while they are also not the present value because
        # the variable costs are included in the oem
        if results_costs == True:
            overall_results = pd.concat([overall_results, pd.DataFrame(columns=[
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

        overall_results = pd.concat([overall_results, pd.DataFrame(columns=[
            'annuity',
            'npv',
            'lcoe',
            'objective_value',
            'simulation_time',
            'comments'])], axis=1, sort=False)

        if number_of_demand_profiles > 1:
            overall_results = pd.concat([overall_results, pd.DataFrame(columns=['demand_profile'])], axis=1)
        for keys in sensitivity_bounds:
            overall_results = pd.concat([overall_results, pd.DataFrame(columns=[keys])], axis=1)

        return overall_results
