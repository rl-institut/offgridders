'''
Small scripts to keep the main file clean
'''

import pandas as pd

from oemof.tools import logger
import logging
try:
    import matplotlib.pyplot as plt
except ImportError:
    print("Matplotlib.pyplot could not be loaded")
    plt = None


class process_input_parameters():

    def list_of_cases(case_definitions):
        case_list = []
        for keys in case_definitions:
            if case_definitions['perform_simulation'] == True: case_list.append(keys)

        str_cases_simulated = ''
        for item in case_list:
            str_cases_simulated = str_cases_simulated + item + ', '

        logging.info('The cases simulated are: base_oem, ' + str_cases_simulated[:-2])
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

        if experiment['coding_process'] == True:
            #todo this is valid even if coding process NOT in place. if evaluated days == 365... so this can be deleted,
            # as well as the item coding process itself can
            '''
            Updating all annuities above to annuities "for the timeframe", so that optimization is based on more adequate 
            costs. Includes project_cost_annuity, distribution_grid_cost_annuity, maingrid_extension_cost_annuity for 
            consistency eventhough these are not used in optimization.
            '''
            from config import evaluated_days
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
            if experiment['white_noise_demand'] != 0:
                experiment.update({'demand':
                                       noise.on_demand(experiment['white_noise_demand'], experiment['demand'])})
            if experiment['white_noise_pv'] != 0:
                experiment.update({'pv_generation_per_kWp':
                                       noise.on_demand(experiment['white_noise_pv'], experiment['pv_generation_per_kWp'])})

            #if experiment['white_noise_wind'] != 0:
            #
            #
    return

    def randomized(white_noise_percentage, data_subframe):
        import numpy as np
        noise = np.random.normal(0, white_noise_percentage, len(data_subframe))
        for i in range(0, len(data_subframe)):
            if data_subframe[i] != 0:
                data_subframe[i] = data_subframe[i] * (1 - noise[i])
        return data_subframe.clip_lower(0)  # do not allow values <0

    def on_demand(white_noise_demand, data_frame):
        """Not completed, adds noise to dict demand"""
        for key in data_frame:
            data_subframe = data_frame[key]
            data_subframe = noise.randomized(white_noise_demand, data_subframe)
            from config import display_graphs_demand
            if display_graphs_demand == True:
                noise.plot_results(data_subframe, "Demand with noise: " + key, "time", "Power in kW")
            data_frame.update({key: data_subframe})
        return  data_frame

    def on_pv(white_noise_irradiation, data_frame):
        """Not completed, adds noise to dict demand"""
        # todo irradiation vs generation
        logging.info("White noise on solar based on irradiation, but is used for generation!")
        data_frame = noise.randomized(white_noise_irradiation, data_frame)
        from config import display_graphs_solar
        if display_graphs_solar == True:
            noise.plot_results(data_frame, "PV generation with noise (only based on irradiation)", "time", "Power in kW")
        return  data_frame

