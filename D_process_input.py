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
                    and case_definitions[case]['based_on_case'] == True:
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
            'wind_cost_capex':
                economics.capex_from_investment(experiment['wind_cost_investment'], experiment['wind_lifetime'],
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
            'wind_cost_annuity':
                economics.annuity(experiment['wind_cost_capex'], experiment['crf'])+experiment['wind_cost_opex'],
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
            'wind_cost_annuity': experiment['wind_cost_annuity'] / 365*experiment['evaluated_days'],
            'genset_cost_annuity': experiment['genset_cost_annuity'] / 365*experiment['evaluated_days'],
            'storage_cost_annuity': experiment['storage_cost_annuity'] / 365*experiment['evaluated_days'],
            'pcoupling_cost_annuity': experiment['pcoupling_cost_annuity'] / 365*experiment['evaluated_days'],
            'project_cost_annuity': experiment['project_cost_annuity'] / 365 * experiment['evaluated_days'],
            'distribution_grid_cost_annuity': experiment['distribution_grid_cost_annuity'] / 365 * experiment['evaluated_days'],
            'maingrid_extension_cost_annuity': experiment['maingrid_extension_cost_annuity'] / 365 * experiment['evaluated_days']
        })

        return experiment

    def add_timeseries(experiment_s):
        # Update experiments and add longest date_time_index to settings
        entries = 0
        longest = ""

        for experiment in experiment_s:
            experiment_s[experiment].update({'time_end': experiment_s[experiment]['time_start']
                                                         + pd.DateOffset(days=experiment_s[experiment]['evaluated_days'])
                                                         - pd.DateOffset(hours=1)})
            #experiment_s[experiment].update({'time_end': experiment_s[experiment]['time_start']+ pd.DateOffset(hours=2)})
            experiment_s[experiment].update({'date_time_index': pd.date_range(start=experiment_s[experiment]['time_start'],
                                                                              end=experiment_s[experiment]['time_end'],
                                                                              freq=experiment_s[experiment]['time_frequency'])})

            if len(experiment_s[experiment]['date_time_index']) > entries:
                entries = len(experiment_s[experiment]['date_time_index'])
                longest = experiment

        max_date_time_index = experiment_s[longest]['date_time_index']
        max_evaluated_days = experiment_s[longest]['evaluated_days']

        for experiment in experiment_s:
                index = experiment_s[experiment]['date_time_index']
                if  experiment_s[experiment]['file_index'] != None:
                    if (experiment_s[experiment]['date_time_index'][0].year != experiment_s[experiment]['demand'].index[0].year):
                        file_index = [item + pd.DateOffset(year=index[0].year) for item in demand.index]
                        # shift to fileindex of data sets to analysed year
                        demand = pd.Series( experiment_s[experiment]['demand'].values, index=experiment_s[experiment]['file_index'])
                        pv_generation_per_kWp = pd.Series( experiment_s[experiment]['pv_generation_per_kWp'].values, index=experiment_s[experiment]['file_index'])
                        wind_generation_per_kW = pd.Series( experiment_s[experiment]['wind_generation_per_kW'].values, index=experiment_s[experiment]['file_index'])
                        # from provided data use only analysed timeframe
                        experiment_s[experiment].update({'demand_profile': demand[index]})
                        experiment_s[experiment].update({'pv_generation_per_kWp': pv_generation_per_kWp[index]})
                        experiment_s[experiment].update({'wind_generation_per_kW': wind_generation_per_kW[index]})

                        if 'grid_availability' in experiment_s[experiment].keys():
                            grid_availability = pd.Series(
                                experiment_s[experiment]['grid_availability'].values,
                                index=experiment_s[experiment]['file_index'])
                            experiment_s[experiment].update({'grid_availability': grid_availability[index]})

                    else:
                        # file index is date time index, no change necessary
                        pass

                elif experiment_s[experiment]['file_index'] == None:
                    # limit based on index
                    experiment_s[experiment].update(
                        {'demand_profile': pd.Series(experiment_s[experiment]['demand'][0:len(index)].values, index=index)})
                    experiment_s[experiment].update(
                        {'pv_generation_per_kWp': pd.Series(experiment_s[experiment]['pv_generation_per_kWp'][0:len(index)].values, index=index)})
                    experiment_s[experiment].update(
                        {'wind_generation_per_kW': pd.Series(experiment_s[experiment]['wind_generation_per_kW'][0:len(index)].values, index=index)})

                    if 'grid_availability' in experiment_s[experiment].keys():
                        experiment_s[experiment].update(
                            {'grid_availability': pd.Series(
                                experiment_s[experiment]['grid_availability'][0:len(index)].values, index=index)})

                else:
                    logging.warning('Project site value "file_index" neither None not non-None.')

                # Used for generation of lp file with only 3-timesteps = Useful to verify optimized equations
                if experiment_s[experiment]['lp_file_for_only_3_timesteps'] == True:
                    experiment_s[experiment].update({'time_start': experiment_s[experiment]['time_start'] + pd.DateOffset(hours=15)})
                    experiment_s[experiment].update({'time_end': experiment_s[experiment]['time_start']+ pd.DateOffset(hours=2)})
                    experiment_s[experiment].update(
                        {'date_time_index': pd.date_range(start=experiment_s[experiment]['time_start'],
                                                          end=experiment_s[experiment]['time_end'],
                                                          freq=experiment_s[experiment]['time_frequency'])})

                    index = experiment_s[experiment]['date_time_index']
                    experiment_s[experiment].update({'demand_profile': experiment_s[experiment]['demand_profile'][index]})
                    experiment_s[experiment].update({'pv_generation_per_kWp': experiment_s[experiment]['pv_generation_per_kWp'][index]})
                    experiment_s[experiment].update({'wind_generation_per_kW': experiment_s[experiment]['wind_generation_per_kW'][index]})
                    if 'grid_availability' in experiment_s[experiment].keys():
                        experiment_s[experiment].update(
                            {'grid_availability': experiment_s[experiment]['grid_availability'][index]})

                experiment_s[experiment].update({
                    'total_demand': sum(experiment_s[experiment]['demand_profile']),
                    'peak_demand': max(experiment_s[experiment]['demand_profile']),
                    'peak_pv_generation_per_kWp': max(experiment_s[experiment]['pv_generation_per_kWp']),
                    'peak_wind_generation_per_kW': max(experiment_s[experiment]['wind_generation_per_kW'])})

                if experiment_s[experiment]['total_demand']==0:
                    logging.warning('No demand in evaluated timesteps at project site ' + experiment_s[experiment]['project_site_name'] + ' - simulation will crash.')
                if experiment_s[experiment]['peak_pv_generation_per_kWp']==0:
                    logging.info('No pv generation in evaluated timesteps at project site ' + experiment_s[experiment]['project_site_name'] + '.')
                if experiment_s[experiment]['peak_wind_generation_per_kW']==0:
                    logging.info('No wind generation in evaluated timesteps at project site ' + experiment_s[experiment]['project_site_name'] + '.')

        return max_date_time_index, max_evaluated_days

class noise:
    def apply(experiment_s):
        for experiment in experiment_s:
            noise.on_series(experiment_s[experiment], 'white_noise_demand', 'demand')
            noise.on_series(experiment_s[experiment], 'white_noise_pv', 'pv_generation_per_kWp')
            noise.on_series(experiment_s[experiment], 'white_noise_wind', 'wind_generation_per_kW')
        return

    def on_series(experiment, noise_name, series_name):
        if experiment[noise_name] != 0:
            series_values = pd.Series(noise.randomized(experiment[noise_name], experiment[series_name]),
                               index=experiment[series_name].index)
            experiment.update({series_name: series_values})
            # add display of series with noise
        return

    def randomized(white_noise_percentage, data_subframe):
        import numpy as np
        noise = np.random.normal(0, white_noise_percentage, len(data_subframe))
        for i in range(0, len(data_subframe)):
            if data_subframe[i] != 0:
                data_subframe[i] = data_subframe[i] * (1 - noise[i])
        return data_subframe.clip_lower(0)  # do not allow values <0

