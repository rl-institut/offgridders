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
        from config import simulated_cases
        listof_cases = []
        for keys in simulated_cases:
            if simulated_cases[keys] == True: listof_cases.append(keys)

        str_cases_simulated = ''
        for item in listof_cases:
            str_cases_simulated = str_cases_simulated + item + ', '

        logging.info('The cases simulated are: ' + str_cases_simulated[:-2])
        return listof_cases

    def input_data(experiment):

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
                experiment['project_life'], experiment['wacc'], experiment['tax'])
            })

        # Annuities of components including opex AND capex
        experiment.update({
            'pv_cost_annuity':
                economics.annuity(experiment['pv_cost_capex']+experiment['pv_cost_opex'], experiment['crf']),
            'genset_cost_annuity':
                economics.annuity(experiment['genset_cost_capex']+experiment['genset_cost_opex'], experiment['crf']),
            'storage_cost_annuity':
                economics.annuity(experiment['storage_cost_capex']+experiment['storage_cost_opex'], experiment['crf']),
            'pcoupling_cost_annuity':
                economics.annuity(experiment['pcoupling_cost_capex']+experiment['pcoupling_cost_opex'], experiment['crf']),
            'project_cost_annuity':
                economics.annuity(experiment['project_cost_fix']+experiment['project_cost_opex'], experiment['crf'])
            })

        # todo economic values for distribution grid are not included yet

        from config import coding_process
        if coding_process == True:
            from config import evaluated_days
            experiment.update({
                'pv_cost_annuity': experiment['pv_cost_annuity'] / 365*evaluated_days,
                'genset_cost_annuity': experiment['genset_cost_annuity'] / 365*evaluated_days,
                'storage_cost_annuity': experiment['storage_cost_annuity'] / 365*evaluated_days,
                'pcoupling_cost_annuity': experiment['pcoupling_cost_annuity'] / 365*evaluated_days
            })

        return experiment

'''
The handler for information on the specific case analysed in the case study ("experiment")
'''

class helpers:
    # todo better display of plots
    def plot_results(pandas_dataframe, title, xaxis, yaxis):
        if plt is not None:
            # Plot demand
            ax = pandas_dataframe.plot()
            ax.set_title(title)
            ax.set_xlabel(xaxis)
            ax.set_ylabel(yaxis)
            plt.show()
        return

    def store_result_matrix(overall_results, case_name, experiment, oemof_results, duration):
        round_to_comma = 5
        result_vector = []
        for item in overall_results.columns.values:
            if item == 'Case':
                result_vector.extend([case_name])
            elif item ==  'Filename':
                result_vector.extend(['results_'+case_name+experiment['filename']])
            elif item == 'Capacity PV kWp':
                result_vector.extend([round(oemof_results['pv_invest_kW'], round_to_comma)])
            elif item ==  'Capacity storage kWh':
                result_vector.extend([round(oemof_results['storage_invest_kWh'], round_to_comma)])
            elif item ==  'Capacity genset kW':
                result_vector.extend([round(oemof_results['genset_invest_kW'], round_to_comma)])
            elif item ==  'Renewable Factor':
                result_vector.extend([round(oemof_results['res_share'], round_to_comma)])
            elif item ==  'NPV':
                result_vector.extend([round(oemof_results['NPV'], round_to_comma)])
            elif item ==  'LCOE':
                result_vector.extend([round(oemof_results['LCOE'], round_to_comma)])
            elif item ==  'Annuity':
                result_vector.extend([round(oemof_results['Annuity'], round_to_comma)])
            elif item ==  'Fuel consumption':
                result_vector.extend([round(oemof_results['fuel_consumption'], round_to_comma)])
            elif item ==  'Simulation time':
                result_vector.extend([round(duration, round_to_comma)])
            elif item == 'demand_profile':
                result_vector.extend([experiment[item]])
            else:
                result_vector.extend([round(experiment[item], round_to_comma)])

        overall_results = overall_results.append(pd.Series(result_vector, overall_results.columns.values),
                                                 ignore_index=True)
        return overall_results

class extract():
    def fuel(experiment):
        experiment_fuel = {}
        experiment_fuel.update({'price_fuel': experiment['price_fuel']})
        experiment_fuel.update({'combustion_value_fuel': experiment['combustion_value_fuel']})
        experiment_fuel.update({'min_res_share': experiment['min_res_share']})
        experiment_fuel.update({'genset_efficiency': experiment['genset_efficiency']})
        return experiment_fuel

    def shortage(experiment):
        experiment_shortage = {}
        experiment_shortage.update({'max_share_unsupplied_load': experiment['max_share_unsupplied_load']})
        experiment_shortage.update({'var_costs_unsupplied_load': experiment['var_costs_unsupplied_load']})
        return experiment_shortage

    def maingrid(experiment):
        experiment_maingrid = {}
        experiment_maingrid.update({'price_electricity_main_grid': experiment['price_electricity_main_grid']})
        return experiment_maingrid

    def storage(experiment):
        experiment_storage = {}
        experiment_storage.update({'storage_cost_annuity': experiment['storage_cost_annuity']})
        experiment_storage.update({'storage_cost_var': experiment['storage_cost_var']})
        experiment_storage.update({'storage_Crate': experiment['storage_Crate']})
        experiment_storage.update({'storage_capacity_max': experiment['storage_capacity_max']})
        experiment_storage.update({'storage_capacity_min': experiment['storage_capacity_min']})
        experiment_storage.update({'storage_initial_soc': experiment['storage_initial_soc']})
        experiment_storage.update({'storage_loss_timestep': experiment['storage_loss_timestep']})
        experiment_storage.update({'storage_inflow_efficiency': experiment['storage_inflow_efficiency']})
        experiment_storage.update({'storage_outflow_efficiency': experiment['storage_outflow_efficiency']})
        return experiment_storage

    def process_oem(experiment):
        experiment_oem = {}
        experiment_oem.update({'storage_Crate': experiment['storage_Crate']})
        experiment_oem.update({'annuity_factor': experiment['annuity_factor']})
        return experiment_oem

    def pcoupling(experiment):
        experiment_pcoupling = {}
        experiment_pcoupling.update({'pcoupling_cost_annuity': experiment['pcoupling_cost_annuity']})
        experiment_pcoupling.update({'pcoupling_cost_var': experiment['pcoupling_cost_var']})
        experiment_pcoupling.update({'pcoupling_efficiency': experiment['pcoupling_efficiency']})
        return experiment_pcoupling

    def genset(experiment):
        experiment_generator = {}
        experiment_generator.update({'genset_cost_annuity': experiment['genset_cost_annuity']})
        experiment_generator.update({'genset_cost_var': experiment['genset_cost_var']})
        experiment_generator.update({'genset_efficiency': experiment['genset_efficiency']})
        experiment_generator.update({'genset_min_loading': experiment['genset_min_loading']})
        experiment_generator.update({'genset_max_loading': experiment['genset_max_loading']})
        return experiment_generator

    def pv(experiment):
        experiment_pv = {}
        experiment_pv.update({'pv_cost_annuity': experiment['pv_cost_annuity']})
        experiment_pv.update({'pv_cost_var': experiment['pv_cost_var']})
        return experiment_pv

    def process_fix(experiment):
        experiment_fix = {}
        experiment_fix.update({'pv_cost_annuity': experiment['pv_cost_annuity']})
        experiment_fix.update({'genset_cost_annuity': experiment['genset_cost_annuity']})
        experiment_fix.update({'pcoupling_cost_annuity': experiment['pcoupling_cost_annuity']})
        experiment_fix.update({'storage_cost_annuity': experiment['storage_cost_annuity']})
        experiment_fix.update({'annuity_factor': experiment['annuity_factor']})
        return experiment_fix

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
        number_of_investments = int(round(project_life / lifetime))

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
