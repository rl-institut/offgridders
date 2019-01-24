'''
Small scripts to keep the main file clean
'''

import pandas as pd

import logging

from Z_economic_functions import economics

class process_input_parameters():
    def list_of_cases(case_definitions):
        case_list = []
        str_cases_simulated = ''
        # Certain ORDER of simulation: First base capacities are optimized
        for case in case_definitions:
            if case_definitions[case]['perform_simulation'] == True \
                    and case_definitions[case]['based_on_case']==False:
                case_list.append(case)
                str_cases_simulated += case + ', '

        logging.info('Base capacities provided by: ' + str_cases_simulated[:-2])

        for case in case_definitions:
            if case_definitions[case]['perform_simulation'] == True \
                    and case_definitions[case]['based_on_case'] == False:
                case_list.append(case)
                str_cases_simulated += case + ', '

        logging.info('All simulated cases: ' + str_cases_simulated[:-2])
        return case_list

    def economic_values(experiment):
        """Pre-processing of input data (calculation of economic values)"""
        experiment.update({'annuity_factor': economics.annuity_factor(experiment['project_life'], experiment['wacc'])})
        experiment.update({'crf': economics.crf(experiment['project_life'], experiment['wacc'])})

        # Capex DO NOT include OPEX costs per year. But they are included in the annuity!
        experiment.update({
            'pv_cost_capex':
                economics.capex_from_investment(experiment['pv_cost_investment'], experiment['pv_lifetime'],
                experiment['project_life'], experiment['wacc'], experiment['tax']),
            'genset_cost_capex':
                economics.capex_from_investment(experiment['genset_cost_investment'], experiment['genset_lifetime'],
                experiment['project_life'], experiment['wacc'], experiment['tax']),
            'storage_cost_capex':
                economics.capex_from_investment( experiment['storage_cost_investment'], experiment['storage_lifetime'],
                experiment['project_life'], experiment['wacc'], experiment['tax']),
            'pcoupling_cost_capex':
                economics.capex_from_investment(experiment['pcoupling_cost_investment'], experiment['pcoupling_lifetime'],
                experiment['project_life'], experiment['wacc'], experiment['tax']),
            'maingrid_extension_cost_capex':
                economics.capex_from_investment(experiment['maingrid_extension_cost_investment'],
                                                experiment['maingrid_extension_lifetime'],
                                                experiment['project_life'], experiment['wacc'], experiment['tax']),
            'distribution_grid_cost_capex':
                economics.capex_from_investment(experiment['distribution_grid_cost_investment'],
                                                experiment['distribution_grid_lifetime'],
                                                experiment['project_life'], experiment['wacc'], experiment['tax'])
            })

        # Annuities of components including opex AND capex
        experiment.update({
            'pv_cost_annuity':
                economics.annuity(experiment['pv_cost_capex'], experiment['crf'])+experiment['pv_cost_opex'],
            'genset_cost_annuity':
                economics.annuity(experiment['genset_cost_capex'], experiment['crf'])+experiment['genset_cost_opex'],
            'storage_cost_annuity':
                economics.annuity(experiment['storage_cost_capex'], experiment['crf'])+experiment['storage_cost_opex'],
            'pcoupling_cost_annuity':
                economics.annuity(experiment['pcoupling_cost_capex'], experiment['crf'])+experiment['pcoupling_cost_opex'],
            'project_cost_annuity':
                economics.annuity(experiment['project_cost_fix'], experiment['crf'])+experiment['project_cost_opex'],
            'maingrid_extension_cost_annuity':
                economics.annuity(experiment['maingrid_extension_cost_capex'], experiment['crf']) + experiment['maingrid_extension_cost_opex'],
            'distribution_grid_cost_annuity':
                economics.annuity(experiment['distribution_grid_cost_capex'], experiment['crf']) + experiment['distribution_grid_cost_opex'],
            })

        '''
        Updating all annuities above to annuities "for the timeframe", so that optimization is based on more adequate 
        costs. Includes project_cost_annuity, distribution_grid_cost_annuity, maingrid_extension_cost_annuity for 
        consistency eventhough these are not used in optimization.
        '''
        experiment.update({
            'pv_cost_annuity': experiment['pv_cost_annuity'] / 365*experiment['evaluated_days'],
            'genset_cost_annuity': experiment['genset_cost_annuity'] / 365*experiment['evaluated_days'],
            'storage_cost_annuity': experiment['storage_cost_annuity'] / 365*experiment['evaluated_days'],
            'pcoupling_cost_annuity': experiment['pcoupling_cost_annuity'] / 365*experiment['evaluated_days'],
            'project_cost_annuity': experiment['project_cost_annuity'] / 365 * experiment['evaluated_days'],
            'distribution_grid_cost_annuity': experiment['distribution_grid_cost_annuity'] / 365 * experiment['evaluated_days'],
            'maingrid_extension_cost_annuity': experiment['maingrid_extension_cost_annuity'] / 365 * experiment['evaluated_days']
        })

        return experiment

class noise:
    def apply(experiments):
        for experiment in experiments:
            noise.on_series(experiments[experiment], 'white_noise_demand', 'demand')
            noise.on_series(experiments[experiment], 'white_noise_pv', 'pv_generation_per_kWp')
            # noise.on_series(sensitivity_experiment_s[experiment], 'white_noise_wind', 'wind_generation_per_kW')

        return

    def on_series(experiment, noise_name, series_name):
        if experiment[noise_name] != 0:
            series_values = pd.Series(noise.randomized(experiment[noise_name], experiment[series_name]),
                               index=experiment[series_name].index)
            experiment.update({series_name: series_values})
            # todo add display of series with noise
        return

    def randomized(white_noise_percentage, data_subframe):
        import numpy as np
        noise = np.random.normal(0, white_noise_percentage, len(data_subframe))
        for i in range(0, len(data_subframe)):
            if data_subframe[i] != 0:
                data_subframe[i] = data_subframe[i] * (1 - noise[i])
        return data_subframe.clip_lower(0)  # do not allow values <0

