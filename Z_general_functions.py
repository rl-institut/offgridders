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

    def define_base_capacities(oemof_results):
        capacities_base = {
            'capacity_pv_kWp': oemof_results['capacity_pv_kWp'],
            'capacity_wind_kW': oemof_results['capacity_wind_kW'],
            'capacity_storage_kWh': oemof_results['capacity_storage_kWh'],
            'capacity_genset_kW': oemof_results['capacity_genset_kW'],
            'capacity_pcoupling_kW': oemof_results['capacity_pcoupling_kW']}
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
            # extend by name of demand profile
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
