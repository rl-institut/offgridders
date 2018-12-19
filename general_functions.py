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


class config_func():
    def cases():
        """Creating list of cases to be analysed based on config file"""
        from config import simulated_cases
        listof_cases = []
        for keys in simulated_cases:
            if simulated_cases[keys] == True: listof_cases.append(keys)

        str_cases_simulated = ''
        for item in listof_cases:
            str_cases_simulated = str_cases_simulated + item + ', '

        logging.info('The cases simulated are: base_oem, ' + str_cases_simulated[:-2])
        return listof_cases

    def input_data(experiment):
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

        from config import coding_process
        if coding_process == True:
            '''
            Updating all annuities above to annuities "for the timeframe", so that optimization is based on more adequate 
            costs. Includes project_cost_annuity, distribution_grid_cost_annuity, maingrid_extension_cost_annuity for 
            consistency eventhough these are not used in optimization.
            '''
            from config import evaluated_days
            experiment.update({
                'pv_cost_annuity': experiment['pv_cost_annuity'] / 365*evaluated_days,
                'genset_cost_annuity': experiment['genset_cost_annuity'] / 365*evaluated_days,
                'storage_cost_annuity': experiment['storage_cost_annuity'] / 365*evaluated_days,
                'pcoupling_cost_annuity': experiment['pcoupling_cost_annuity'] / 365*evaluated_days,
                'project_cost_annuity': experiment['project_cost_annuity'] / 365 * evaluated_days,
                'distribution_grid_cost_annuity': experiment['distribution_grid_cost_annuity'] / 365 * evaluated_days,
                'maingrid_extension_cost_annuity': experiment['maingrid_extension_cost_annuity'] / 365 * evaluated_days
            })

        return experiment

    def check_results_dir():
        """ Checking for output folder, creating it if nonexistant and deleting files if needed """
        import os
        from config import output_folder, restore_oemof_if_existant
        if os.path.isdir(output_folder)!=True:
            os.mkdir(output_folder)
        if os.path.isdir(output_folder  +   '/oemof') != True:
                os.mkdir(output_folder  +   '/oemof')
        if os.path.isdir(output_folder  +   '/lp_files') != True:
                os.mkdir(output_folder  +   '/lp_files')
        if os.path.isdir(output_folder  +   '/storage') != True:
                os.mkdir(output_folder  +   '/storage')
        if os.path.isdir(output_folder  +   '/electricity_mg') != True:
                os.mkdir(output_folder  +   '/electricity_mg')

        else:
            if restore_oemof_if_existant == False:
                #list_of_folders = [output_folder, output_folder  +   "/oemof", output_folder  +   "/storage", output_folder  +   "/electricity_bus"]
                #for folder in list_of_folders:
                for root, dirs, files in os.walk(folder):
                    for f in files:
                        os.remove(folder+'/'+f)
                logging.info('Deleted all files in folder "simulation_results".')
        return

class helpers:

    def noise(white_noise_percentage, data_subframe):
        import numpy as np
        noise = np.random.normal(0, white_noise_percentage, len(data_subframe))
        for i in range(0, len(data_subframe)):
            if data_subframe[i]!=0:
                data_subframe[i]=data_subframe[i] * (1 - noise[i])
        return data_subframe.clip_lower(0) # do not allow values <0

    def noise_demand(white_noise_demand, data_frame):
        """Not completed, adds noise to dict demand"""
        for key in data_frame:
            data_subframe = data_frame[key]
            data_subframe = helpers.noise(white_noise_demand, data_subframe)
            from config import display_graphs_demand
            if display_graphs_demand == True:
                helpers.plot_results(data_subframe, "Demand with noise: "+key, "time", "Power in kW")
            data_frame.update({key: data_subframe})
        return  data_frame

    def noise_pv(white_noise_irradiation, data_frame):
        """Not completed, adds noise to dict demand"""
        # todo irradiation vs generation
        logging.info("White noise on solar based on irradiation, but is used for generation!")
        data_frame = helpers.noise(white_noise_irradiation, data_frame)
        from config import display_graphs_solar
        if display_graphs_solar == True:
            helpers.plot_results(data_frame, "PV generation with noise (only based on irradiation)", "time", "Power in kW")
        return  data_frame

    # todo better display of plots
    def plot_results(pandas_dataframe, title, xaxis, yaxis):
        """ general function for plots"""
        if plt is not None:
            # Plot demand
            ax = pandas_dataframe.plot()
            ax.set_title(title)
            ax.set_xlabel(xaxis)
            ax.set_ylabel(yaxis)
            plt.show()
        return


    def store_result_matrix(overall_results, experiment, oemof_results, duration):
        """
        Storing results to vector and then result matrix for saving it in csv.
        """
        round_to_comma = 5
        result_series = pd.Series()

        for key in overall_results.columns.values:
            # Check if called value is in oemof results -> Remember: check if pandas index has certain index: pd.object.index.contains(key)
            if key in oemof_results:
                if isinstance(oemof_results[key],str):
                    result_series = result_series.append(
                        pd.Series([oemof_results[key]], index=[key]))
                else:
                    result_series = result_series.append(
                        pd.Series([round(oemof_results[key], round_to_comma)], index=[key]))
            # extend by simulation time
            elif key == 'simulation_time':
                oemof_results.update({key: round(duration, round_to_comma)})
                result_series = result_series.append(pd.Series([round(duration, round_to_comma)], index=[key]))
            # extend by name of demand profile
            elif key == 'demand_profile':
                result_series = result_series.append(pd.Series([experiment[key]], index=[key]))
            # Check if called value is a parameter of experiments
            elif key in experiment:
                result_series = result_series.append(
                    pd.Series([round(experiment[key], round_to_comma)], index=[key]))

        result_series = result_series.reindex(overall_results.columns, fill_value=None)

        overall_results = overall_results.append(pd.Series(result_series),
                                                 ignore_index=True)
        return overall_results

""" All economic functions"""
class economics():
    # annuity factor to calculate present value of cash flows
    def annuity_factor(project_life, wacc):
        # discount_rate was replaced here by wacc
        annuity_factor = 1 / wacc - 1 / (wacc * (1 + wacc) ** project_life)
        return annuity_factor

    # accounting factor to translate present value to annual cash flows
    def crf(project_life, wacc):
        crf = (wacc * (1+ wacc) ** project_life) / ((1+wacc) ** project_life - 1)
        return crf

    def capex_from_investment(investment_t0, lifetime, project_life, wacc, tax):
        # [quantity, investment, installation, weight, lifetime, om, first_investment]
        number_of_investments = int(round(project_life / lifetime+0.5))

        # costs with quantity and import tax at t=0
        first_time_investment = investment_t0 * (1+tax)

        for count_of_replacements in range(0, number_of_investments):
            # Very first investment is in year 0
            if count_of_replacements == 0:
                capex = first_time_investment
            else:
                # replacements taking place in year = number_of_replacement * lifetime
                if count_of_replacements * lifetime != project_life:
                    capex = capex + first_time_investment / ((1 + wacc) ** (count_of_replacements * lifetime))

        # Substraction of component value at end of life with last replacement (= number_of_investments - 1)
        if number_of_investments * lifetime > project_life:
            last_investment = first_time_investment / ((1 + wacc) ** ((number_of_investments - 1) * lifetime))
            linear_depreciation_last_investment = last_investment / lifetime
            capex = capex -  linear_depreciation_last_investment * (number_of_investments * lifetime - project_life)

        return capex

    def annuity(present_value, crf):
        annuity = present_value * crf
        return  annuity

    def present_value_from_annuity(annuity, annuity_factor):
        present_value = annuity * annuity_factor
        return present_value

