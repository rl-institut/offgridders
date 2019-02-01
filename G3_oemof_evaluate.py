"""
Requires:
oemof, matplotlib, demandlib, pvlib
tables, tkinter
"""

import pandas as pd
import oemof.outputlib as outputlib

import logging

# Try to import matplotlib librar
try:
    import matplotlib.pyplot as plt
except ImportError:
    logging.warning('Attention! matplotlib could not be imported.')
    plt = None

class utilities:
    def join_e_flows_df(timeseries, name, e_flows_df):
        new_column = pd.DataFrame(timeseries.values, columns=[name], index=timeseries.index)
        e_flows_df = e_flows_df.join(new_column)
        return e_flows_df

    def annual_value(name, timeseries, oemof_results, case_dict):
        value = sum(timeseries)
        value = value * 365 / case_dict['evaluated_days']
        oemof_results.update({name: value})
        return

class timeseries:
    def get_demand(case_dict, oemof_results, electricity_bus):
        # Get flow
        demand = electricity_bus['sequences'][(('bus_electricity_mg', 'sink_demand'), 'flow')]
        e_flows_df = pd.DataFrame(demand.values, columns=['Demand'], index=demand.index)
        utilities.annual_value('total_demand_annual_kWh', demand, oemof_results, case_dict)
        oemof_results.update({'demand_peak_kW': max(demand)})
        return e_flows_df
    
    def get_shortage(case_dict, oemof_results, electricity_bus, e_flows_df):
        # Get flow
        if case_dict['allow_shortage'] == True:
            shortage = electricity_bus['sequences'][(('source_shortage', 'bus_electricity_mg'), 'flow')]
            demand_supplied = e_flows_df['Demand'] - shortage
            utilities.annual_value('total_demand_supplied_annual_kWh', demand_supplied, oemof_results,case_dict)
            utilities.annual_value('total_demand_shortage_annual_kWh', shortage, oemof_results,case_dict)
            e_flows_df = utilities.join_e_flows_df(shortage, 'Demand shortage', e_flows_df)
            e_flows_df = utilities.join_e_flows_df(demand_supplied, 'Demand supplied', e_flows_df)
        else:
            oemof_results.update({'total_demand_supplied_annual_kWh': oemof_results['total_demand_annual_kWh']})
            oemof_results.update({'total_demand_shortage_annual_kWh': 0})
        return e_flows_df

    def get_excess(case_dict, oemof_results, electricity_bus, e_flows_df):
        # Get flow
        excess = electricity_bus['sequences'][(('bus_electricity_mg', 'sink_excess'), 'flow')]
        e_flows_df = utilities.join_e_flows_df(excess, 'Excess generation', e_flows_df)
        utilities.annual_value('total_demand_excess_annual_kWh', excess, oemof_results, case_dict) # not given as result.csv right now
        return e_flows_df

    def get_pv(case_dict, oemof_results, electricity_bus, e_flows_df, pv_generation_max):
        # Get flow
        if case_dict['pv_fixed_capacity'] != None:
            pv_gen = electricity_bus['sequences'][(('source_pv', 'bus_electricity_mg'), 'flow')]
            utilities.annual_value('total_pv_generation_kWh', pv_gen, oemof_results, case_dict)
            e_flows_df = utilities.join_e_flows_df(pv_gen, 'PV generation', e_flows_df)
        else:
            oemof_results.update({'total_pv_generation_kWh': 0})

        # Get capacity
        if case_dict['pv_fixed_capacity'] == False:
            if pv_generation_max > 1:
                oemof_results.update({'capacity_pv_kWp': electricity_bus['scalars'][(('source_pv', 'bus_electricity_mg'), 'invest')]* pv_generation_max })
            elif pv_generation_max > 0 and pv_generation_max < 1:
                oemof_results.update({'capacity_pv_kWp': electricity_bus['scalars'][(('source_pv', 'bus_electricity_mg'), 'invest')] / pv_generation_max })
            else:
                logging.warning("Error, Strange PV behaviour (PV gen < 0)")
        elif isinstance(case_dict['pv_fixed_capacity'], float):
                oemof_results.update({'capacity_pv_kWp': case_dict['pv_fixed_capacity']})
        elif case_dict['pv_fixed_capacity'] == None:
            oemof_results.update({'capacity_pv_kWp': 0})
        return e_flows_df

    def get_wind(case_dict, oemof_results, electricity_bus, e_flows_df, wind_generation_max):
        # Get flow
        if case_dict['wind_fixed_capacity'] != None:
            wind_gen = electricity_bus['sequences'][(('source_wind', 'bus_electricity_mg'), 'flow')]
            utilities.annual_value('total_wind_generation_kWh', wind_gen, oemof_results, case_dict)
            e_flows_df = utilities.join_e_flows_df(wind_gen, 'Wind generation', e_flows_df)
        else:
            oemof_results.update({'total_wind_generation_kWh': 0})

        # Get capacity
        if case_dict['wind_fixed_capacity'] == False:
            if wind_generation_max > 1:
                oemof_results.update({'capacity_wind_kW': electricity_bus['scalars'][(('source_wind', 'bus_electricity_mg'), 'invest')]* wind_generation_max })
            elif wind_generation_max > 0 and wind_generation_max < 1:
                oemof_results.update({'capacity_wind_kW': electricity_bus['scalars'][(('source_wind', 'bus_electricity_mg'), 'invest')] / wind_generation_max })
            else:
                logging.warning("Error, Strange Wind behaviour (Wind gen < 0)")
        elif isinstance(case_dict['wind_fixed_capacity'], float):
                oemof_results.update({'capacity_wind_kW': case_dict['wind_fixed_capacity']})
        elif case_dict['wind_fixed_capacity'] == None:
            oemof_results.update({'capacity_wind_kW': 0})
        return e_flows_df

    def get_genset(case_dict, oemof_results, electricity_bus, e_flows_df):
        # Get flow
        if case_dict['genset_fixed_capacity'] != None:
            genset = electricity_bus['sequences'][(('transformer_genset', 'bus_electricity_mg'), 'flow')]
            utilities.annual_value('total_genset_generation_kWh', genset, oemof_results, case_dict)
            e_flows_df = utilities.join_e_flows_df(genset, 'Genset generation', e_flows_df)
        else:
            oemof_results.update({'total_genset_generation_kWh': 0})

        # Get capacity
        if case_dict['genset_fixed_capacity'] == False:
            # Optimized generator capacity
            oemof_results.update({'capacity_genset_kW': electricity_bus['scalars'][(('transformer_genset', 'bus_electricity_mg'), 'invest')]})
        elif isinstance(case_dict['genset_fixed_capacity'], float):
            oemof_results.update({'capacity_genset_kW': case_dict['genset_fixed_capacity']})
        elif case_dict['genset_fixed_capacity']==None:
            oemof_results.update({'capacity_genset_kW': 0})
        return e_flows_df

    def get_fuel(case_dict, oemof_results, results):
        if case_dict['genset_fixed_capacity'] != None:
            fuel_bus = outputlib.views.node(results, 'bus_fuel')
            fuel = fuel_bus['sequences'][(('source_fuel', 'bus_fuel'), 'flow')]
            utilities.annual_value('consumption_fuel_annual_l', fuel, oemof_results, case_dict)
        else:
            oemof_results.update({'consumption_fuel_annual_l': 0})
        return

    def get_storage(case_dict, oemof_results, experiment, results, e_flows_df):
        # Get flow
        if case_dict['storage_fixed_capacity'] != None:
            storage = outputlib.views.node(results, 'generic_storage')
            storage_discharge = storage['sequences'][(('generic_storage', 'bus_electricity_mg'), 'flow')]
            storage_charge = storage['sequences'][(('bus_electricity_mg', 'generic_storage'), 'flow')]
            stored_capacity = storage['sequences'][(('generic_storage', 'None'), 'capacity')]
            utilities.annual_value('total_battery_throughput_kWh', storage_charge, oemof_results, case_dict)
            e_flows_df = utilities.join_e_flows_df(storage_charge, 'Storage charge', e_flows_df)
            e_flows_df = utilities.join_e_flows_df(storage_discharge, 'Storage discharge', e_flows_df)
            e_flows_df = utilities.join_e_flows_df(stored_capacity, 'Stored capacity', e_flows_df)
        else:
            oemof_results.update({'total_battery_throughput_kWh': 0})

        # Get capacity
        #todo cant this be shortened as well?!
        if case_dict['storage_fixed_capacity'] == False:
            # Optimized storage capacity
            # todo not most elegantly solves, das electrcity bus is called a sevcond time here...
            electricity_bus = outputlib.views.node(results, 'bus_electricity_mg')
            capacity_battery = electricity_bus['scalars'][(('bus_electricity_mg', 'generic_storage'), 'invest')]/experiment['storage_Crate_charge']
            # possibly using generic_storage['scalars'][((generic_storage, None), invest)]
            oemof_results.update({'capacity_storage_kWh': capacity_battery})
        elif isinstance(case_dict['storage_fixed_capacity'], float):
            oemof_results.update({'capacity_storage_kWh': case_dict['storage_fixed_capacity']})
        elif case_dict['storage_fixed_capacity'] == None:
            oemof_results.update({'capacity_storage_kWh': 0})
        return e_flows_df

    def get_national_grid(case_dict, oemof_results, results, e_flows_df, grid_availability):
        micro_grid_bus = outputlib.views.node(results, 'bus_electricity_mg')
        if case_dict['pcc_consumption_fixed_capacity'] != None or case_dict['pcc_feedin_fixed_capacity'] != None:
            national_grid_bus = outputlib.views.node(results, 'bus_electricity_ng')
        # todo if we really use setting_pcc_utility_owned and it influences the revenue, we have to use it in oemof object definitions as well!

        #from config import setting_pcc_utility_owned
        # if utility owned, these pcc_cap costs would actually NOT be in the LCOE, rigfht?
        # decision: timeseries will always be the one for the mg side. but the accumulated value can be different.
        # todo still decide with of the flows to include in e_flow_df, and which ones to put into oemof results for cost calculation (expenditures, revenues)
        # Get flow

        # define grid availability
        if case_dict['pcc_consumption_fixed_capacity'] != None or case_dict['pcc_feedin_fixed_capacity'] != None:
            e_flows_df = utilities.join_e_flows_df(grid_availability, 'Grid availability', e_flows_df)
        else:
            grid_availability_symbolic = pd.Series([0 for i in e_flows_df.index], index=e_flows_df.index)
            e_flows_df = utilities.join_e_flows_df(grid_availability_symbolic, 'Grid availability', e_flows_df)

        if case_dict['pcc_consumption_fixed_capacity'] != None:
            consumption_mg_side = micro_grid_bus['sequences'][(('transformer_pcc_consumption', 'bus_electricity_mg'), 'flow')]
            e_flows_df = utilities.join_e_flows_df(consumption_mg_side, 'Consumption from main grid (MG side)', e_flows_df)
            utilities.annual_value('consumption_main_grid_mg_side_annual_kWh', consumption_mg_side, oemof_results, case_dict)

            consumption_utility_side = national_grid_bus['sequences'][(('bus_electricity_ng', 'transformer_pcc_consumption'), 'flow')]
            e_flows_df = utilities.join_e_flows_df(consumption_utility_side, 'Consumption from main grid (utility side)', e_flows_df)
            utilities.annual_value('consumption_main_grid_utility_side_annual_kWh', consumption_utility_side, oemof_results,
                                   case_dict)
            # todo dependent on from config import setting_pcc_utility_owned either choose first or last for expenditures!
            # if setting_pcc_utility_owned == True:
        else:
            oemof_results.update({'consumption_main_grid_mg_side_annual_kWh': 0,
                                  'consumption_main_grid_utility_side_annual_kWh': 0})

        if case_dict['pcc_feedin_fixed_capacity'] != None:
            feedin_mg_side = micro_grid_bus['sequences'][(('bus_electricity_mg', 'transformer_pcc_feedin'), 'flow')]
            e_flows_df = utilities.join_e_flows_df(feedin_mg_side, 'Feed into main grid (MG side)', e_flows_df)
            utilities.annual_value('feedin_main_grid_mg_side_annual_kWh', feedin_mg_side, oemof_results, case_dict)

            feedin_utility_side = national_grid_bus['sequences'][(('transformer_pcc_feedin', 'bus_electricity_ng'), 'flow')]
            e_flows_df = utilities.join_e_flows_df(feedin_utility_side, 'Feed into main grid (utility side)', e_flows_df)
            utilities.annual_value('feedin_main_grid_utility_side_annual_kWh', feedin_utility_side, oemof_results, case_dict)
        else:
            oemof_results.update({'feedin_main_grid_mg_side_annual_kWh': 0,
                                  'feedin_main_grid_utility_side_annual_kWh': 0})

        # get capacities
        if case_dict['pcc_consumption_fixed_capacity'] != None or case_dict['pcc_feedin_fixed_capacity'] != None:
            pcc_cap = []
            if case_dict['pcc_consumption_fixed_capacity'] == False:
                pcc_cap.append(consumption_utility_side.max())
            elif isinstance(case_dict['pcc_consumption_fixed_capacity'], float):
                pcc_cap.append(case_dict['pcc_consumption_fixed_capacity'])

            if case_dict['pcc_feedin_fixed_capacity'] == False:
                pcc_cap.append(feedin_utility_side.max())
            elif isinstance(case_dict['pcc_feedin_fixed_capacity'], float):
                pcc_cap.append(case_dict['pcc_feedin_fixed_capacity'])

            oemof_results.update({'capacity_pcoupling_kW': max(pcc_cap)})
        elif case_dict['pcc_consumption_fixed_capacity'] == None and case_dict['pcc_feedin_fixed_capacity'] == None:
            oemof_results.update({'capacity_pcoupling_kW': 0})
        else:
            logging.warning("Invalid value of pcc_consumption_fixed_capacity and/or pcc_feedin_fixed_capacity.")

        #todo change or describe where costs and revenues are generated at main grid interconenection
        total_pcoupling_throughput_kWh = 0
        if case_dict['pcc_consumption_fixed_capacity'] != None or case_dict['pcc_feedin_fixed_capacity'] != None:
            if case_dict['pcc_consumption_fixed_capacity'] != None:
                total_pcoupling_throughput_kWh += oemof_results['consumption_main_grid_mg_side_annual_kWh'] # payments also for inverter loss
            if case_dict['pcc_feedin_fixed_capacity'] != None:
                total_pcoupling_throughput_kWh += oemof_results['feedin_main_grid_mg_side_annual_kWh']

        oemof_results.update({'total_pcoupling_throughput_kWh':   total_pcoupling_throughput_kWh})

        return e_flows_df

    def get_res_share(case_dict, oemof_results, experiment):

        total_generation = oemof_results['total_genset_generation_kWh']
        total_generation += oemof_results['consumption_main_grid_mg_side_annual_kWh']
        #total_generation += oemof_results['total_wind_generation_kWh']
        total_generation += oemof_results['total_pv_generation_kWh']
        total_generation += oemof_results['total_wind_generation_kWh']

        total_fossil_generation = oemof_results['total_genset_generation_kWh']
        # attention: only effectively used electricity consumption counts for renewable share
        total_fossil_generation += oemof_results['consumption_main_grid_mg_side_annual_kWh'] * (1 - experiment['maingrid_renewable_share'])

        res_share = abs(1 - total_fossil_generation / total_generation)

        oemof_results.update({'res_share': res_share})
        return

