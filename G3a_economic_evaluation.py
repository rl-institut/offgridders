###############################################################################
# Imports and initialize
###############################################################################

import logging

# Try to import matplotlib librar
try:
    import matplotlib.pyplot as plt
except ImportError:
    logging.warning('Attention! matplotlib could not be imported.')
    plt = None

###############################################################################
#
###############################################################################
class economic_evaluation():

    def project_annuities(case_dict, oemof_results, experiment):
        # Define all annuities based on component capacities (Capex+Opex), add var. operational costs
        # Extrapolate to costs of whole year
        economic_evaluation.annuities_365(case_dict, oemof_results, experiment)

        # Add costs related to annuities
        economic_evaluation.costs(oemof_results, experiment)

        # Expenditures for fuel
        economic_evaluation.expenditures_fuel(oemof_results, experiment)

        # Expenditures for shortage
        economic_evaluation.expenditures_shortage(oemof_results, experiment)

        if case_dict['pcc_consumption_fixed_capacity'] != None:
            #---------Expenditures from electricity consumption from main grid ----------#
            economic_evaluation.expenditures_main_grid_consumption(oemof_results, experiment)

        if case_dict['pcc_feedin_fixed_capacity'] != None:
            # ---------Revenues from electricity feed-in to main grid ----------#
            economic_evaluation.revenue_main_grid_feedin(oemof_results, experiment)

        oemof_results.update({
            'npv': oemof_results['annuity'] * experiment['annuity_factor'],
            'lcoe': oemof_results['annuity'] / oemof_results['total_demand_supplied_annual_kWh']
        })
        return

    def annuities_365(case_dict, oemof_results, experiment):
        evaluated_days = case_dict['evaluated_days']

        logging.debug('Economic evaluation. Calculating investment costs over analysed timeframe.')
        interval_annuity={
            'annuity_pv': experiment['pv_cost_annuity'] * oemof_results['capacity_pv_kWp'],
            'annuity_wind': experiment['wind_cost_annuity'] * oemof_results['capacity_wind_kW'],
            'annuity_storage': experiment['storage_cost_annuity'] * oemof_results['capacity_storage_kWh'],
            'annuity_genset': experiment['genset_cost_annuity'] * oemof_results['capacity_genset_kW'],
            'annuity_project': experiment['project_cost_annuity'],
            'annuity_distribution_grid': experiment['distribution_grid_cost_annuity']}

        if case_dict['pcc_consumption_fixed_capacity'] != None and case_dict['pcc_feedin_fixed_capacity'] != None:
            interval_annuity.update({'annuity_pcoupling': 2*experiment['pcoupling_cost_annuity'] * oemof_results['capacity_pcoupling_kW']})
        else:
            interval_annuity.update({'annuity_pcoupling': experiment['pcoupling_cost_annuity'] * oemof_results['capacity_pcoupling_kW']})

        # Main grid extension
        if case_dict['pcc_consumption_fixed_capacity'] != None or case_dict['pcc_feedin_fixed_capacity'] != None:
            interval_annuity.update({
                'annuity_grid_extension':
                    experiment['maingrid_extension_cost_annuity'] * experiment['maingrid_distance']})
        else:
            interval_annuity.update({'annuity_grid_extension': 0})

        logging.debug('Economic evaluation. Calculating O&M costs over analysed timeframe.')
        om_var_interval={
            'om_var_pv': oemof_results['total_pv_generation_kWh']*experiment['pv_cost_var'],
            'om_var_wind': oemof_results['total_wind_generation_kWh'] * experiment['wind_cost_var'],
            'om_var_storage': oemof_results['total_battery_throughput_kWh']*experiment['storage_cost_var'],
            'om_var_genset': oemof_results['total_genset_generation_kWh']*experiment['genset_cost_var'],
            'om_var_pcoupling': oemof_results['total_pcoupling_throughput_kWh']*experiment['pcoupling_cost_var']
        }

        logging.debug('Economic evaluation. Scaling investment costs and O&M to year.')
        oemof_results.update({
            'annuity_pv':
                (interval_annuity['annuity_pv'] + om_var_interval['om_var_pv'])* 365 / evaluated_days,
            'annuity_wind':
                (interval_annuity['annuity_wind'] + om_var_interval['om_var_wind'])* 365 / evaluated_days,
            'annuity_storage':
                (interval_annuity['annuity_storage'] + om_var_interval['om_var_storage'])* 365 / evaluated_days,
            'annuity_genset':
                (interval_annuity['annuity_genset'] + om_var_interval['om_var_genset'])* 365 / evaluated_days,
            'annuity_pcoupling':
                (interval_annuity['annuity_pcoupling'] + om_var_interval['om_var_pcoupling'])* 365 / evaluated_days,
            'annuity_project':
                (interval_annuity['annuity_project'])* 365 / evaluated_days,
            'annuity_distribution_grid':
                (interval_annuity['annuity_distribution_grid'])* 365 / evaluated_days,
            'annuity_grid_extension':
                (interval_annuity['annuity_grid_extension'])* 365 / evaluated_days})

        oemof_results.update({'annuity': oemof_results['annuity_pv']
                                         + oemof_results['annuity_wind']
                                         + oemof_results['annuity_storage']
                                         + oemof_results['annuity_genset']
                                         + oemof_results['annuity_pcoupling']
                                         + oemof_results['annuity_project']
                                         + oemof_results['annuity_distribution_grid']
                                         + oemof_results['annuity_grid_extension']})

        return

    def costs(oemof_results, experiment):
        logging.debug('Economic evaluation. Calculating present costs.')
        oemof_results.update({
            'costs_pv': oemof_results['annuity_pv'] * experiment['annuity_factor'],
            'costs_wind': oemof_results['annuity_wind'] * experiment['annuity_factor'],
            'costs_storage': oemof_results['annuity_storage'] * experiment['annuity_factor'],
            'costs_genset': oemof_results['annuity_genset'] * experiment['annuity_factor'],
            'costs_pcoupling': oemof_results['annuity_pcoupling'] * experiment['annuity_factor'],
            'costs_project': oemof_results['annuity_project'] * experiment['annuity_factor'],
            'costs_distribution_grid': oemof_results['annuity_distribution_grid'] * experiment['annuity_factor'],
            'costs_grid_extension': oemof_results['annuity_grid_extension'] * experiment['annuity_factor']
        })
        return

    def expenditures_fuel(oemof_results, experiment):
        logging.debug('Economic evaluation. Calculating fuel consumption and expenditures.')
        oemof_results.update({'expenditures_fuel_annual':
                oemof_results['consumption_fuel_annual_l'] * experiment['price_fuel'] / experiment['combustion_value_fuel']})

        oemof_results.update({'expenditures_fuel_total':
                oemof_results['expenditures_fuel_annual'] * experiment['annuity_factor']})

        oemof_results.update({'annuity': oemof_results['annuity'] + oemof_results['expenditures_fuel_annual']})
        return

    def expenditures_main_grid_consumption(oemof_results, experiment):
        logging.debug('Economic evaluation. Calculating main grid consumption and expenditures.')
        # Necessary in oemof_results: consumption_main_grid_annual
        oemof_results.update({'expenditures_main_grid_consumption_annual':
                oemof_results['consumption_main_grid_mg_side_annual_kWh'] * experiment['maingrid_electricity_price']})

        oemof_results.update({'expenditures_main_grid_consumption_total':
                oemof_results['expenditures_main_grid_consumption_annual'] * experiment['annuity_factor']})

        oemof_results.update({'annuity': oemof_results['annuity'] + oemof_results['expenditures_main_grid_consumption_annual']})
        return

    def expenditures_shortage(oemof_results, experiment):
        logging.debug('Economic evaluation. Calculating shortage and expenditures.')
        # Necessary in oemof_results: consumption_main_grid_annual
        oemof_results.update({'expenditures_shortage_annual':
                 oemof_results['total_demand_shortage_annual_kWh'] * experiment['shortage_penalty_costs']})

        oemof_results.update({'expenditures_shortage_total':
                oemof_results['expenditures_shortage_annual'] * experiment['annuity_factor']})

        oemof_results.update({'annuity': oemof_results['annuity'] + oemof_results['expenditures_shortage_annual']})
        return

    def revenue_main_grid_feedin(oemof_results, experiment):
        logging.debug('Economic evaluation. Calculating feeding and revenues.')
        oemof_results.update({'revenue_main_grid_feedin_annual':
                - oemof_results['feedin_main_grid_mg_side_annual_kWh'] * experiment['maingrid_feedin_tariff']})

        oemof_results.update({'revenue_main_grid_feedin_total':
                oemof_results['revenue_main_grid_feedin_annual'] * experiment['annuity_factor']})

        oemof_results.update(
            {'annuity': oemof_results['annuity'] + oemof_results['revenue_main_grid_feedin_annual']})
        return

class process():
    def annual_value(value, evaluated_days):
        value = value * 365 / evaluated_days

