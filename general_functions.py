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
        experiment_storage.update({'cost_annuity_storage': experiment['cost_annuity_storage']})
        experiment_storage.update({'cost_var_storage': experiment['cost_var_storage']})
        experiment_storage.update({'storage_Crate': experiment['storage_Crate']})
        experiment_storage.update({'storage_capacity_max': experiment['storage_capacity_max']})
        experiment_storage.update({'storage_capacity_min': experiment['storage_capacity_min']})
        experiment_storage.update({'storage_initial_soc': experiment['storage_initial_soc']})
        experiment_storage.update({'storage_loss_timestep': experiment['storage_loss_timestep']})
        experiment_storage.update({'storage_inflow_efficiency': experiment['storage_inflow_efficiency']})
        experiment_storage.update({'storage_outflow_efficiency': experiment['storage_outflow_efficiency']})
        return experiment_storage

    def storage_oem(experiment):
        experiment_storage = {}
        experiment_storage.update({'storage_Crate': experiment['storage_Crate']})
        return experiment_storage

    def pcoupling(experiment):
        experiment_pcoupling = {}
        experiment_pcoupling.update({'cost_annuity_pcoupling': experiment['cost_annuity_pcoupling']})
        experiment_pcoupling.update({'cost_var_pcoupling': experiment['cost_var_pcoupling']})
        experiment_pcoupling.update({'efficiency_pcoupling': experiment['efficiency_pcoupling']})
        return experiment_pcoupling

    def genset(experiment):
        experiment_generator = {}
        experiment_generator.update({'cost_annuity_genset': experiment['cost_annuity_genset']})
        experiment_generator.update({'cost_var_genset': experiment['cost_var_genset']})
        experiment_generator.update({'genset_efficiency': experiment['genset_efficiency']})
        experiment_generator.update({'genset_min_loading': experiment['genset_min_loading']})
        experiment_generator.update({'genset_max_loading': experiment['genset_max_loading']})
        return experiment_generator

    def pv(experiment):
        experiment_pv = {}
        experiment_pv.update({'cost_annuity_pv': experiment['cost_annuity_pv']})
        experiment_pv.update({'cost_var_pv': experiment['cost_var_pv']})
        return experiment_pv