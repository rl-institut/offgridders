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

class helpers:
    # currently not used
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

    def define_base_capacities(oemof_results):
        capacities_base = {
            'capacity_pv_kWp': oemof_results['capacity_pv_kWp'],
            'capacity_wind_kW': oemof_results['capacity_wind_kW'],
            'capacity_storage_kWh': oemof_results['capacity_storage_kWh'],
            'power_storage_kW': oemof_results['power_storage_kW'],
            'capacity_genset_kW': oemof_results['capacity_genset_kW'],
            'capacity_pcoupling_kW': oemof_results['capacity_pcoupling_kW'],
            'capacity_rectifier_ac_dc_kW': oemof_results['capacity_rectifier_ac_dc_kW'],
            'capacity_inverter_dc_ac_kW': oemof_results['capacity_inverter_dc_ac_kW']}
        return capacities_base

    def store_result_matrix(overall_results, experiment, oemof_results):
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
            # extend by item of demand profile
            elif key == 'demand_profile':
                result_series = result_series.append(pd.Series([experiment[key]], index=[key]))
            # Check if called value is a parameter of sensitivity_experiment_s
            elif key in experiment:
                if isinstance(experiment[key], str):
                    result_series = result_series.append(
                        pd.Series([experiment[key]], index=[key]))
                else:
                    result_series = result_series.append(
                    pd.Series([round(experiment[key], round_to_comma)], index=[key]))

        result_series = result_series.reindex(overall_results.columns, fill_value=None)

        overall_results = overall_results.append(pd.Series(result_series),
                                                 ignore_index=True)
        return overall_results

    def test_techno_economical_parameters_complete(experiment):
        parameter_list = {
            'blackout_duration':	0,
            'blackout_duration_std_deviation':	0,
            'blackout_frequency':	0,
            'blackout_frequency_std_deviation':	0,
            'combustion_value_fuel':	9.8,
            'demand_ac_scaling_factor':	1,
            'demand_dc_scaling_factor':	1,
            'distribution_grid_cost_investment':	0,
            'distribution_grid_cost_opex':	0,
            'distribution_grid_lifetime':	0,
            'genset_batch':	1,
            'genset_cost_investment':	0,
            'genset_cost_opex':	0,
            'genset_cost_var':	0,
            'genset_efficiency':	0.33,
            'genset_lifetime':	15,
            'genset_max_loading':	1,
            'genset_min_loading':	0,
            'genset_oversize_factor':	1.2,
            'inverter_dc_ac_batch':	1,
            'inverter_dc_ac_cost_investment':	0,
            'inverter_dc_ac_cost_opex':	0,
            'inverter_dc_ac_cost_var':	0,
            'inverter_dc_ac_efficiency':	1,
            'inverter_dc_ac_lifetime':	15,
            'maingrid_distance':	0,
            'maingrid_electricity_price':	0.15,
            'maingrid_extension_cost_investment':	0,
            'maingrid_extension_cost_opex':	0,
            'maingrid_extension_lifetime':	40,
            'maingrid_feedin_tariff':	0,
            'maingrid_renewable_share':	0,
            'min_renewable_share':	0,
            'pcoupling_batch':	1,
            'pcoupling_cost_investment':	0,
            'pcoupling_cost_opex':	0,
            'pcoupling_cost_var':	0,
            'pcoupling_efficiency': 1,
            'pcoupling_lifetime':	15,
            'pcoupling_oversize_factor':	1.05,
            'price_fuel':	0.76,
            'project_cost_investment':	0,
            'project_cost_opex':	0,
            'project_lifetime':	20,
            'pv_batch':	1,
            'pv_cost_investment':	0,
            'pv_cost_opex':	0,
            'pv_cost_var':	0,
            'pv_lifetime':	20,
            'rectifier_ac_dc_batch':	1,
            'rectifier_ac_dc_cost_investment':	0,
            'rectifier_ac_dc_cost_opex':	0,
            'rectifier_ac_dc_cost_var':	0,
            'rectifier_ac_dc_efficiency':	1,
            'rectifier_ac_dc_lifetime':	15,
            'shortage_max_allowed':	0,
            'shortage_max_timestep':	1,
            'shortage_penalty_costs':	0.2,
            'stability_limit':	0.4,
            'storage_batch_capacity': 1,
            'storage_batch_power': 1,
            'storage_capacity_cost_investment': 0,
            'storage_capacity_cost_opex': 0,
            'storage_capacity_lifetime': 5,
            'storage_cost_var': 0,
            'storage_Crate_charge': 1,
            'storage_Crate_discharge': 1,
            'storage_efficiency_charge': 0.8,
            'storage_efficiency_discharge': 1,
            'storage_loss_timestep': 0,
            'storage_power_cost_investment': 0,
            'storage_power_cost_opex': 0,
            'storage_power_lifetime': 5,
            'storage_soc_initial': None,
            'storage_soc_max': 0.95,
            'storage_soc_min': 0.3,
            'tax':	0,
            'wacc':	0.09,
            'white_noise_demand':	0,
            'white_noise_pv':	0,
            'white_noise_wind':	0,
            'wind_batch':	1,
            'wind_cost_investment':	0,
            'wind_cost_opex':	0,
            'wind_cost_var':	0,
            'wind_lifetime':    15}

        for parameter in parameter_list:
            if parameter not in experiment:
                logging.warning('Parameter "' + parameter + '" missing. Do you use an old excel-template? \n'
                                +'    ' + '    ' + '    ' + 'Simulation will continue with generic value of "' + parameter
                                + '": ' + str(parameter_list[parameter]))

                experiment.update({parameter: parameter_list[parameter]})