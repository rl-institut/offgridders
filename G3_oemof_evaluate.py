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
    def get_demand(case_dict, oemof_results, electricity_bus_ac, electricity_bus_dc, experiment):
        logging.debug('Evaluate flow: demand')
        # Get flow

        e_flows_df = pd.DataFrame([0 for i in experiment['date_time_index']], columns=['Demand'], index=experiment['date_time_index'])

        #if case_dict['genset_fixed_capacity'] != None \
        #        or case_dict['wind_fixed_capacity'] != None \
        #        or case_dict['pcc_consumption_fixed_capacity'] != None \
        #        or case_dict['pcc_feedin_fixed_capacity'] != None:

        demand_ac = electricity_bus_ac['sequences'][(('bus_electricity_ac', 'sink_demand_ac'), 'flow')]
        e_flows_df = utilities.join_e_flows_df(demand_ac, 'Demand AC', e_flows_df)
        if case_dict['evaluation_perspective'] == 'AC_bus':
            e_flows_df['Demand'] += demand_ac
        else:
            e_flows_df['Demand'] += demand_ac / experiment['inverter_dc_ac_efficiency']

        #if case_dict['pv_fixed_capacity'] != None \
        #        or case_dict['storage_fixed_capacity'] != None:

        demand_dc = electricity_bus_dc['sequences'][(('bus_electricity_dc', 'sink_demand_dc'), 'flow')]
        e_flows_df = utilities.join_e_flows_df(demand_dc, 'Demand DC', e_flows_df)
        if case_dict['evaluation_perspective'] == 'AC_bus':
            e_flows_df['Demand'] += demand_dc / experiment['rectifier_ac_dc_efficiency']
        else:
            e_flows_df['Demand'] += demand_dc

        utilities.annual_value('total_demand_annual_kWh', e_flows_df['Demand'], oemof_results, case_dict)
        oemof_results.update({'demand_peak_kW': max(e_flows_df['Demand'])})
        return e_flows_df
    
    def get_shortage(case_dict, oemof_results, electricity_bus_ac, electricity_bus_dc, experiment, e_flows_df):
        logging.debug('Evaluate flow: shortage')

        # Get flow
        shortage = pd.Series([0 for i in e_flows_df.index], index=e_flows_df.index)

        if case_dict['allow_shortage'] == True:
            if electricity_bus_ac != None:

                shortage_ac = electricity_bus_ac['sequences'][(('source_shortage', 'bus_electricity_ac'), 'flow')]
                utilities.annual_value('total_demand_shortage_ac_annual_kWh', shortage_ac, oemof_results, case_dict)
                e_flows_df = utilities.join_e_flows_df(shortage_ac, 'Demand shortage AC', e_flows_df)

                if case_dict['evaluation_perspective'] == 'AC_bus':
                    shortage += shortage_ac
                else:
                    shortage += shortage_ac / experiment['inverter_dc_ac_efficiency']

            if electricity_bus_dc != None:

                shortage_dc = electricity_bus_dc['sequences'][(('source_shortage', 'bus_electricity_dc'), 'flow')]
                utilities.annual_value('total_demand_shortage_dc_annual_kWh', shortage_dc, oemof_results, case_dict)
                e_flows_df = utilities.join_e_flows_df(shortage_dc, 'Demand shortage DC', e_flows_df)

                if case_dict['evaluation_perspective'] == 'AC_bus':
                    shortage += shortage_dc / experiment['rectifier_ac_dc_efficiency']
                else:
                    shortage += shortage_dc

            demand_supplied = e_flows_df['Demand'] - shortage
            utilities.annual_value('total_demand_supplied_annual_kWh', demand_supplied, oemof_results, case_dict)
            utilities.annual_value('total_demand_shortage_annual_kWh', shortage, oemof_results,case_dict)
            e_flows_df = utilities.join_e_flows_df(shortage, 'Demand shortage', e_flows_df)
            e_flows_df = utilities.join_e_flows_df(demand_supplied, 'Demand supplied', e_flows_df)
        else:
            oemof_results.update({'total_demand_supplied_annual_kWh': oemof_results['total_demand_annual_kWh']})
            oemof_results.update({'total_demand_shortage_annual_kWh': 0})
        return e_flows_df

    def get_excess(case_dict, oemof_results, electricity_bus_ac, electricity_bus_dc, e_flows_df):
        logging.debug('Evaluate excess: ')
        # Get flow
        excess = pd.Series([0 for i in e_flows_df.index], index=e_flows_df.index)

        if electricity_bus_ac != None:

            excess_ac = electricity_bus_ac['sequences'][(('bus_electricity_ac', 'sink_excess'), 'flow')]
            excess += excess_ac
            utilities.annual_value('total_demand_excess_ac_annual_kWh', excess_ac, oemof_results, case_dict)
            e_flows_df = utilities.join_e_flows_df(excess_ac, 'Excess generation AC', e_flows_df)

        if electricity_bus_dc != None:

            excess_dc = electricity_bus_dc['sequences'][(('bus_electricity_dc', 'sink_excess'), 'flow')]
            excess += excess_dc
            utilities.annual_value('total_demand_excess_dc_annual_kWh', excess, oemof_results, case_dict) # not given as result.csv right now
            e_flows_df = utilities.join_e_flows_df(excess_dc, 'Excess generation DC', e_flows_df)

        utilities.annual_value('total_demand_excess_annual_kWh', excess, oemof_results, case_dict)  # not given as result.csv right now
        e_flows_df = utilities.join_e_flows_df(excess, 'Excess generation', e_flows_df)

        return e_flows_df

    def get_pv(case_dict, oemof_results, electricity_bus_dc, experiment, e_flows_df, pv_generation_max):
        logging.debug('Evaluate flow: pv')
        # Get flow
        if case_dict['pv_fixed_capacity'] != None:
            pv_gen = electricity_bus_dc['sequences'][(('source_pv', 'bus_electricity_dc'), 'flow')]
            utilities.annual_value('total_pv_generation_kWh', pv_gen, oemof_results, case_dict)
            e_flows_df = utilities.join_e_flows_df(pv_gen, 'PV generation DC', e_flows_df)
            if case_dict['evaluation_perspective'] == 'AC_bus':
                e_flows_df = utilities.join_e_flows_df(pv_gen / experiment['rectifier_ac_dc_efficiency'],
                                                       'PV generation AC', e_flows_df)

            if case_dict['evaluation_perspective'] == 'AC_bus':
                e_flows_df = utilities.join_e_flows_df(e_flows_df['PV generation AC'], 'PV generation', e_flows_df)
            else:
                e_flows_df = utilities.join_e_flows_df(e_flows_df['PV generation DC'], 'PV generation', e_flows_df)
        else:
            oemof_results.update({'total_pv_generation_kWh': 0})

        # Get capacity
        if case_dict['pv_fixed_capacity'] == False:
            if pv_generation_max > 1:
                oemof_results.update({'capacity_pv_kWp': electricity_bus_dc['scalars'][(('source_pv', 'bus_electricity_dc'), 'invest')]* pv_generation_max })
            elif pv_generation_max > 0 and pv_generation_max < 1:
                oemof_results.update({'capacity_pv_kWp': electricity_bus_dc['scalars'][(('source_pv', 'bus_electricity_dc'), 'invest')] / pv_generation_max })
            else:
                logging.warning("Error, Strange PV behaviour (PV gen < 0)")
        elif isinstance(case_dict['pv_fixed_capacity'], float):
                oemof_results.update({'capacity_pv_kWp': case_dict['pv_fixed_capacity']})
        elif case_dict['pv_fixed_capacity'] == None:
            oemof_results.update({'capacity_pv_kWp': 0})
        return e_flows_df

    def get_rectifier(case_dict, oemof_results, electricity_bus_ac, electricity_bus_dc, e_flows_df):
        logging.debug('Evaluate flow: rectifier')
        # Get flow
        if case_dict['rectifier_ac_dc_fixed_capacity'] != None:
            rectifier_out = electricity_bus_dc['sequences'][(('transformer_rectifier', 'bus_electricity_dc'), 'flow')]
            e_flows_df = utilities.join_e_flows_df(rectifier_out, 'Rectifier output', e_flows_df)

            rectifier_in = electricity_bus_ac['sequences'][(('bus_electricity_ac', 'transformer_rectifier'), 'flow')]
            e_flows_df = utilities.join_e_flows_df(rectifier_in, 'Rectifier input', e_flows_df)

            utilities.annual_value('total_rectifier_ac_dc_throughput_kWh', rectifier_in, oemof_results, case_dict)
        else:
            oemof_results.update({'total_rectifier_ac_dc_throughput_kWh': 0})

        # Get capacity
        if case_dict['rectifier_ac_dc_fixed_capacity'] == False:
            rectifier_capacity = electricity_bus_ac['scalars'][(('bus_electricity_ac', 'transformer_rectifier'), 'invest')]
            oemof_results.update({'capacity_rectifier_ac_dc_kW': rectifier_capacity})

        elif isinstance(case_dict['rectifier_ac_dc_fixed_capacity'], float):
            oemof_results.update({'capacity_rectifier_ac_dc_kW': case_dict['rectifier_ac_dc_fixed_capacity']})

        elif case_dict['rectifier_ac_dc_fixed_capacity']==None:
            oemof_results.update({'capacity_rectifier_ac_dc_kW': 0})
        return e_flows_df

    def get_inverter(case_dict, oemof_results, electricity_bus_ac, electricity_bus_dc, e_flows_df):
        logging.debug('Evaluate flow: rectifier')
        # Get flow
        if case_dict['inverter_dc_ac_fixed_capacity'] != None:
            inverter_out = electricity_bus_ac['sequences'][(('transformer_inverter_dc_ac', 'bus_electricity_ac'), 'flow')]
            e_flows_df = utilities.join_e_flows_df(inverter_out, 'Inverter output', e_flows_df)

            inverter_in = electricity_bus_dc['sequences'][(('bus_electricity_dc', 'transformer_inverter_dc_ac'), 'flow')]
            e_flows_df = utilities.join_e_flows_df(inverter_in, 'Inverter input', e_flows_df)

            utilities.annual_value('total_inverter_dc_ac_throughput_kWh', inverter_in, oemof_results, case_dict)
        else:
            oemof_results.update({'total_inverter_dc_ac_throughput_kWh': 0})

        # Get capacity
        if case_dict['inverter_dc_ac_fixed_capacity'] == False:
            rectifier_capacity = electricity_bus_dc['scalars'][
                (('bus_electricity_dc', 'transformer_inverter_dc_ac'), 'invest')]
            oemof_results.update({'capacity_inverter_dc_ac_kW': rectifier_capacity})

        elif isinstance(case_dict['inverter_dc_ac_fixed_capacity'], float):
            oemof_results.update({'capacity_inverter_dc_ac_kW': case_dict['inverter_dc_ac_fixed_capacity']})

        elif case_dict['inverter_dc_ac_fixed_capacity'] == None:
            oemof_results.update({'capacity_inverter_dc_ac_kW': 0})
        return e_flows_df

    def get_wind(case_dict, oemof_results, electricity_bus_ac, e_flows_df, wind_generation_max):
        logging.debug('Evaluate flow: wind')
        # Get flow
        if case_dict['wind_fixed_capacity'] != None:
            wind_gen = electricity_bus_ac['sequences'][(('source_wind', 'bus_electricity_ac'), 'flow')]
            utilities.annual_value('total_wind_generation_kWh', wind_gen, oemof_results, case_dict)
            e_flows_df = utilities.join_e_flows_df(wind_gen, 'Wind generation', e_flows_df)
        else:
            oemof_results.update({'total_wind_generation_kWh': 0})

        # Get capacity
        if case_dict['wind_fixed_capacity'] == False:
            if wind_generation_max > 1:
                oemof_results.update({'capacity_wind_kW': electricity_bus_ac['scalars'][(('source_wind', 'bus_electricity_ac'), 'invest')]* wind_generation_max })
            elif wind_generation_max > 0 and wind_generation_max < 1:
                oemof_results.update({'capacity_wind_kW': electricity_bus_ac['scalars'][(('source_wind', 'bus_electricity_ac'), 'invest')] / wind_generation_max })
            else:
                logging.warning("Error, Strange Wind behaviour (Wind gen < 0)")
        elif isinstance(case_dict['wind_fixed_capacity'], float):
                oemof_results.update({'capacity_wind_kW': case_dict['wind_fixed_capacity']})
        elif case_dict['wind_fixed_capacity'] == None:
            oemof_results.update({'capacity_wind_kW': 0})
        return e_flows_df

    def get_genset(case_dict, oemof_results, electricity_bus_ac, e_flows_df):
        logging.debug('Evaluate flow: genset')
        # Get flow
        if case_dict['genset_fixed_capacity'] != None:
            genset = electricity_bus_ac['sequences'][(('transformer_genset_1', 'bus_electricity_ac'), 'flow')]
            e_flows_df = utilities.join_e_flows_df(genset, 'Genset 1 generation', e_flows_df)
            total_genset = genset
            for number in range(2, case_dict['number_of_equal_generators']+1):
                genset = electricity_bus_ac['sequences'][(('transformer_genset_' + str(number), 'bus_electricity_ac'), 'flow')]
                e_flows_df = utilities.join_e_flows_df(genset, 'Genset '+str(number)+ ' generation', e_flows_df)
                total_genset += genset
            utilities.annual_value('total_genset_generation_kWh', total_genset, oemof_results, case_dict)
            e_flows_df = utilities.join_e_flows_df(total_genset, 'Genset generation', e_flows_df)
        else:
            oemof_results.update({'total_genset_generation_kWh': 0})

        # Get capacity
        if case_dict['genset_fixed_capacity'] == False:
            # Optimized generator capacity (sum)
            genset_capacity = 0
            for number in range(1, case_dict['number_of_equal_generators'] + 1):
                genset_capacity += electricity_bus_ac['scalars'][(('transformer_genset_' + str(number), 'bus_electricity_ac'), 'invest')]
            oemof_results.update({'capacity_genset_kW': genset_capacity})
        elif isinstance(case_dict['genset_fixed_capacity'], float):
            oemof_results.update({'capacity_genset_kW': case_dict['genset_fixed_capacity']})
        elif case_dict['genset_fixed_capacity']==None:
            oemof_results.update({'capacity_genset_kW': 0})
        return e_flows_df

    def get_fuel(case_dict, oemof_results, results):
        logging.debug('Evaluate flow: fuel')
        if case_dict['genset_fixed_capacity'] != None:
            fuel_bus = outputlib.views.node(results, 'bus_fuel')
            fuel = fuel_bus['sequences'][(('source_fuel', 'bus_fuel'), 'flow')]
            utilities.annual_value('consumption_fuel_annual_l', fuel, oemof_results, case_dict)
        else:
            oemof_results.update({'consumption_fuel_annual_l': 0})
        return

    def get_storage(case_dict, oemof_results, experiment, results, e_flows_df):
        logging.debug('Evaluate flow: storage')
        # Get flow
        if case_dict['storage_fixed_capacity'] != None:
            storage = outputlib.views.node(results, 'generic_storage')
            storage_discharge = storage['sequences'][(('generic_storage', 'bus_electricity_dc'), 'flow')]
            storage_charge = storage['sequences'][(('bus_electricity_dc', 'generic_storage'), 'flow')]
            stored_capacity = storage['sequences'][(('generic_storage', 'None'), 'capacity')]
            utilities.annual_value('total_storage_throughput_kWh', storage_charge, oemof_results, case_dict)

            e_flows_df = utilities.join_e_flows_df(storage_charge, 'Storage charge DC', e_flows_df)
            e_flows_df = utilities.join_e_flows_df(storage_discharge, 'Storage discharge DC', e_flows_df)
            e_flows_df = utilities.join_e_flows_df(stored_capacity, 'Stored capacity', e_flows_df)

            if case_dict['evaluation_perspective'] == 'AC_bus':
                e_flows_df = utilities.join_e_flows_df(storage_charge / experiment['rectifier_ac_dc_efficiency'], 'Storage charge AC', e_flows_df)
                e_flows_df = utilities.join_e_flows_df(storage_discharge / experiment['inverter_dc_ac_efficiency'], 'Storage discharge AC', e_flows_df)
                e_flows_df = utilities.join_e_flows_df(e_flows_df['Storage charge AC'], 'Storage charge', e_flows_df)
                e_flows_df = utilities.join_e_flows_df(e_flows_df['Storage discharge AC'], 'Storage discharge',
                                                       e_flows_df)
            else:
                e_flows_df = utilities.join_e_flows_df(e_flows_df['Storage charge DC'], 'Storage charge', e_flows_df)
                e_flows_df = utilities.join_e_flows_df(e_flows_df['Storage discharge DC'], 'Storage discharge',
                                                       e_flows_df)
        else:
            oemof_results.update({'total_storage_throughput_kWh': 0})

        # Get capacity
        if case_dict['storage_fixed_capacity'] == False:
            # Optimized storage capacity
            electricity_bus_dc = outputlib.views.node(results, 'bus_electricity_dc')
            capacity_battery = electricity_bus_dc['scalars'][(('bus_electricity_dc', 'generic_storage'), 'invest')]/experiment['storage_Crate_charge']
            # possibly using generic_storage['scalars'][((generic_storage, None), invest)]
            oemof_results.update({'capacity_storage_kWh': capacity_battery})
        elif isinstance(case_dict['storage_fixed_capacity'], float):
            oemof_results.update({'capacity_storage_kWh': case_dict['storage_fixed_capacity']})
        elif case_dict['storage_fixed_capacity'] == None:
            oemof_results.update({'capacity_storage_kWh': 0})

        #calculate SOC of battery:
        if oemof_results['capacity_storage_kWh']>0:
            e_flows_df = utilities.join_e_flows_df(stored_capacity/oemof_results['capacity_storage_kWh'], 'Storage SOC', e_flows_df)
        else:
            #  todo working?
            e_flows_df = utilities.join_e_flows_df(pd.Series([0 for t in e_flows_df.index], index=e_flows_df.index),
                                                   'Storage SOC', e_flows_df)

        return e_flows_df

    def get_national_grid(case_dict, oemof_results, results, e_flows_df, grid_availability):
        logging.debug('Evaluate flow: main grid')
        micro_grid_bus = outputlib.views.node(results, 'bus_electricity_ac')
        # define grid availability
        if case_dict['pcc_consumption_fixed_capacity'] != None or case_dict['pcc_feedin_fixed_capacity'] != None:
            e_flows_df = utilities.join_e_flows_df(grid_availability, 'Grid availability', e_flows_df)
        else:
            grid_availability_symbolic = pd.Series([0 for i in e_flows_df.index], index=e_flows_df.index)
            e_flows_df = utilities.join_e_flows_df(grid_availability_symbolic, 'Grid availability', e_flows_df)

        if case_dict['pcc_consumption_fixed_capacity'] != None:
            consumption_mg_side = micro_grid_bus['sequences'][(('transformer_pcc_consumption', 'bus_electricity_ac'), 'flow')]
            e_flows_df = utilities.join_e_flows_df(consumption_mg_side, 'Consumption from main grid (MG side)', e_flows_df)
            utilities.annual_value('consumption_main_grid_mg_side_annual_kWh', consumption_mg_side, oemof_results, case_dict)

            bus_electricity_ng_consumption = outputlib.views.node(results, 'bus_electricity_ng_consumption')
            consumption_utility_side = bus_electricity_ng_consumption['sequences'][(('bus_electricity_ng_consumption', 'transformer_pcc_consumption'), 'flow')]
            e_flows_df = utilities.join_e_flows_df(consumption_utility_side, 'Consumption from main grid (utility side)', e_flows_df)
            utilities.annual_value('consumption_main_grid_utility_side_annual_kWh', consumption_utility_side, oemof_results,
                                   case_dict)

        else:
            oemof_results.update({'consumption_main_grid_mg_side_annual_kWh': 0,
                                  'consumption_main_grid_utility_side_annual_kWh': 0})

        oemof_results.update({'autonomy_factor':
                                  (oemof_results['total_demand_supplied_annual_kWh']-oemof_results['consumption_main_grid_mg_side_annual_kWh'])
                                  /oemof_results['total_demand_supplied_annual_kWh']})

        if case_dict['pcc_feedin_fixed_capacity'] != None:
            feedin_mg_side = micro_grid_bus['sequences'][(('bus_electricity_ac', 'transformer_pcc_feedin'), 'flow')]
            e_flows_df = utilities.join_e_flows_df(feedin_mg_side, 'Feed into main grid (MG side)', e_flows_df)
            utilities.annual_value('feedin_main_grid_mg_side_annual_kWh', feedin_mg_side, oemof_results, case_dict)

            bus_electricity_ng_feedin = outputlib.views.node(results, 'bus_electricity_ng_feedin')
            feedin_utility_side = bus_electricity_ng_feedin['sequences'][(('transformer_pcc_feedin', 'bus_electricity_ng_feedin'), 'flow')]
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

        total_pcoupling_throughput_kWh = 0
        if case_dict['pcc_consumption_fixed_capacity'] != None or case_dict['pcc_feedin_fixed_capacity'] != None:
            if case_dict['pcc_consumption_fixed_capacity'] != None:
                total_pcoupling_throughput_kWh += oemof_results['consumption_main_grid_mg_side_annual_kWh'] # payments also for inverter loss
            if case_dict['pcc_feedin_fixed_capacity'] != None:
                total_pcoupling_throughput_kWh += oemof_results['feedin_main_grid_mg_side_annual_kWh']

        oemof_results.update({'total_pcoupling_throughput_kWh':   total_pcoupling_throughput_kWh})

        return e_flows_df

    def get_res_share(case_dict, oemof_results, experiment):
        logging.debug('Evaluate: res share')
        total_generation = oemof_results['total_genset_generation_kWh']
        total_generation += oemof_results['consumption_main_grid_mg_side_annual_kWh']
        total_generation += oemof_results['total_pv_generation_kWh']
        total_generation += oemof_results['total_wind_generation_kWh']

        total_fossil_generation = oemof_results['total_genset_generation_kWh']
        # attention: only effectively used electricity consumption counts for renewable share
        total_fossil_generation += oemof_results['consumption_main_grid_mg_side_annual_kWh'] * (1 - experiment['maingrid_renewable_share'])
        res_share = abs(1 - total_fossil_generation / total_generation)

        oemof_results.update({'res_share': res_share})
        return
