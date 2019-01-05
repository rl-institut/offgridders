
import logging


class evaluate_timeseries:
    def get_all(case_dict, electricity_bus, experiment, grid_availability):

        oemof_results = {
            'case': case_dict['case_name'],
            'filename': 'results_' + case_dict['case_name'] + experiment['filename'],
            'objective_value': meta['objective'],
            'comments': ''
        }

        e_flows_df = pd.DataFrame(grid_availability.values, columns=['Grid availability'], index=grid_availability.index)

        timeseries.get_demand(case_dict, oemof_results, electricity_bus, e_flows_df)
        timeseries.get_shortage(case_dict, oemof_results, electricity_bus, e_flows_df)
        # todo specify reliability into supply_reliability_kWh, national_grid_reliability_h
        oemof_results.update({'supply_reliability':
                                  oemof_results['total_demand_supplied_annual_kWh'] / oemof_results[
                                      'total_demand_annual_kWh']})

        timeseries.get_excess(case_dict, oemof_results, electricity_bus, e_flows_df)
        timeseries.get_pv(case_dict, oemof_results, electricity_bus, e_flows_df)
        timeseries.get_genset(case_dict, oemof_results, electricity_bus, e_flows_df)
        timeseries.get_fuel(case_dict, oemof_results, fuel_bus)

        timeseries.get_shortage(case_dict, oemof_results, electricity_bus, e_flows_df)

        from config import setting_pcc_utility_owned
        # todo still decide with of the flows to include in e_flow_df, and which ones to put into oemof results for cost calculation (expenditures, revenues)
        if setting_pcc_utility_owned == True:
            timeseries.get_feedin_mg_side(case_dict, oemof_results, electricity_bus, e_flows_df)
            timeseries.get_consumption_mg_side(case_dict, oemof_results, electricity_bus, e_flows_df)
        else:
            timeseries.get_feedin_ng_side(case_dict, oemof_results, electricity_bus_ng, e_flows_df)
            timeseries.get_consumption_ng_side(case_dict, oemof_results, electricity_bus_ng, e_flows_df)

        plausability_tests.run(e_flows_df)

        return oemof_results, e_flows_df


class utilities:
    def join_e_flows_df(e_flows_df, timeseries, name):
    e_flows_df = e_flows_df.join(pd.DataFrame(timeseries.values,
                                              columns=[name],
                                              index=timeseries.index))
        return

    def annual_value(name, timeseries, oemof_results, case_dict):
        value = sum(timeseries)
        value = value * 365 / case_dict['evaluated_days']
        oemof_results.update({name: value})
        return

class timeseries:
    def get_demand(case_dict, oemof_results, electricity_bus, e_flows_df):
        demand = electricity_bus['sequences'][(('bus_electricity_mg', 'sink_demand'), 'flow')]
        utilities.join_e_flows_df(e_flows_df, demand, 'Demand')
        utilities.annual_value('total_demand_annual_kWh', demand, oemof_results, case_dict['evaluated_days'])
        oemof_results.update({'demand_peak_kW': max(demand)})
        return e_flows_df
    
    def get_shortage(case_dict, oemof_results, electricity_bus, e_flows_df):
        if case_dict['allow_shortage'] == True:
            shortage = electricity_bus['sequences'][(('source_shortage', 'bus_electricity_mg'), 'flow')]
            demand_supplied = demand - shortage
            utilities.annual_value('total_demand_supplied_annual_kWh', demand_supplied, oemof_results,case_dict['evaluated_days'])
            utilities.annual_value('total_demand_shortage_annual_kWh', shortage, oemof_results,case_dict['evaluated_days'])
            utilities.join_e_flows_df(e_flows_df, shortage, 'Demand shortage')
            utilities.join_e_flows_df(e_flows_df, demand_supplied, 'Demand supplied')
        else:
            oemof_results.update({'total_demand_supplied_annual_kWh': oemof_results['total_demand_annual_kWh']})
        return

    def get_pv(case_dict, oemof_results, electricity_bus, e_flows_df):
        if case_dict['pv_fixed_capacity'] != None:
            pv_gen = electricity_bus['sequences'][(('source_pv', 'bus_electricity_mg'), 'flow')]
            utilities.annual_value('total_pv_generation_kWh', pv_gen, oemof_results, case_dict)
            utilities.join_e_flows_df(e_flows_df, pv_gen, 'PV generation')
        return

    def get_excess(case_dict, oemof_results, electricity_bus, e_flows_df):
        excess = electricity_bus['sequences'][(('bus_electricity_mg', 'sink_excess'), 'flow')]
        utilities.join_e_flows_df(e_flows_df, excess, 'Excess generation')
        utilities.annual_value('total_demand_shortage_annual_kWh', excess, oemof_results, case_dict) # not given as result.csv right now
        return

    def get_genset(case_dict, oemof_results, electricity_bus, e_flows_df):
        if case_dict['genset_fixed_capacity'] != None:
            genset = electricity_bus['sequences'][(('transformer_fuel_generator', 'bus_electricity_mg'), 'flow')]
            utilities.annual_value('total_genset_generation_kWh', genset, oemof_results, case_dict)
            utilities.join_e_flows_df(e_flows_df, genset, 'Genset generation')
        return

    def get_fuel(case_dict, oemof_results, fuel_bus):
        # todo is fuel source only added if genset added?
        # total_fuel_consumption_l = utilities.annual_value(fuel_consumption, case_dict)
        # utilities.annual_value('consumption_fuel_annual_l', genset, oemof_results, case_dict)
        return

    def get_storage(case_dict, oemof_results, electricity_bus, e_flows_df):
        if case_dict['storage_fixed_capacity'] != None:
            storage_discharge = electricity_bus['sequences'][(('generic_storage', 'bus_electricity_mg'), 'flow')]
            storage_charge = electricity_bus['sequences'][(('bus_electricity_mg', 'generic_storage'), 'flow')]
            utilities.annual_value('total_battery_throughput_kWh', storage_charge, oemof_results, case_dict)
            utilities.join_e_flows_df(e_flows_df, storage_charge, 'Storage charge')
            utilities.join_e_flows_df(e_flows_df, storage_discharge, 'Storage discharge')
        return

    # if pcc belongs to utility
    def get_feedin_mg_side(case_dict, oemof_results, electricity_bus_mg, e_flows_df):
        if case_dict['pcc_feedin_fixed_capacity'] != None:
            feedin = electricity_bus_mg['sequences'][(('bus_electricity_mg', 'transformer_pcc_feedin'), 'flow')]
            utilities.join_e_flows_df(e_flows_df, feedin, 'Feed into main grid')
        return

    def get_consumption_mg_side(case_dict, oemof_results, electricity_bus_mg, e_flows_df):
        if case_dict['pcc_consumption_fixed_capacity'] != None:
            consumption = electricity_bus_mg['sequences'][
                (('transformer_pcc_consumption', 'bus_electricity_mg'), 'flow')]
            utilities.join_e_flows_df(e_flows_df, consumption, 'Consumption from main grid')
        return

    # if pcc belongs to mg owner
    def get_feedin_ng_side(case_dict, oemof_results, electricity_bus_ng, e_flows_df):
        if case_dict['pcc_feedin_fixed_capacity'] != None:
            feedin = electricity_bus_ng['sequences'][(('transformer_pcc_feedin', 'electricity_bus_ng'), 'flow')]
            utilities.join_e_flows_df(e_flows_df, feedin, 'Feed into main grid')
        return

    def get_consumption_ng_side(case_dict, oemof_results, electricity_bus_ng, e_flows_df):
        if case_dict['pcc_consumption_fixed_capacity'] != None:
            consumption = electricity_bus_ng['sequences'][
                (('electricity_bus_ng', 'transformer_pcc_consumption'), 'flow')]
            utilities.join_e_flows_df(e_flows_df, consumption, 'Consumption from main grid')
        return

class plausability_tests:
    '''
    e_flows_df can include columns with titles...
    'Demand'
    'Demand shortage'
    'Demand supplied'
    'PV generation'
    'Excess electricity'
    'Consumption from main grid'
    'Feed into main grid'
    'Storage discharge'
    'Storage charge'
    'Genset generation'
    'Excess generation'
    'PV generation'
    'Grid availability'
    '''
    def run(oemof_results, e_flows_df):
        '''
        Checking oemof calculations for plausability. The most obvious errors should be identified this way.
        Ideally, not a single error should be displayed or added to the oemof comments.
        Checks include:
        - storage charge <-> dicharge
        - Demand <-> supplied demand <-> shortage
        - feedin <-> consumption
        - grid availability <-> feedin to grid
        - grid availability <-> consumption from grid
        - excess <-> shortage
        - excess <-> feedin > pcc cap and excess <-> grid availability
        '''
        plausability_tests.charge_discharge(oemof_results, e_flows_df)
        plausability_tests.demand_supply_shortage(oemof_results, e_flows_df)
        plausability_tests.feedin_consumption(oemof_results, e_flows_df)
        plausability_tests.gridavailability_consumption(oemof_results, e_flows_df)
        plausability_tests.gridavailability_feedin(oemof_results, e_flows_df)
        plausability_tests.excess_shortage(oemof_results, e_flows_df)
        plausability_tests.excess_feedin(oemof_results, e_flows_df)
        return


    def charge_discharge (oemof_results, e_flows_df):
        if ('Storage discharge' in e_flows_df.columns and 'Storage charge' in e_flows_df):
            boolean = True
            if any(e_flows_df['Storage discharge'] != 0 and e_flows_df['Storage charge'] != 0):
                boolean = False

            if boolean == False:
                logging.warning("ATTENTION: Charge and discharge of batteries at the same time!")
                oemof_results.update({'comments': oemof_results['comments'] + 'Charge and discharge of batteries at the same time. '})
        return

    def demand_supply_shortage (oemof_results, e_flows_df):

        if (('Demand supplied' in e_flows_df.columns)
                and ('Demand' in e_flows_df.columns)
                and ('Demand shortage' in e_flows_df.columns)):

            boolean = True

            if any(e_flows_df['Demand supplied'] != e_flows_df['Demand'] and e_flows_df['Demand shortage'] == 0):
                boolean = False

            if boolean == False:
                logging.warning("ATTENTION: Demand not fully supplied but no shortage!")
                oemof_results.update({'comments': oemof_results['comments'] + 'Demand not fully supplied but no shortage. '})

        return


    def feedin_consumption(oemof_results, e_flows_df):
        if (('Consumption from main grid' in e_flows_df.columns)
                and ('Feed into main grid' in e_flows_df.columns)):

            boolean = True

            if any(e_flows_df['Consumption from main grid'] != 0 and e_flows_df['Feed into main grid'] != 0):
                boolean = False

            if boolean == False:
                logging.warning("ATTENTION: Feedin to and consumption from national grid at the same time!")
                oemof_results.update(
                    {'comments': oemof_results['comments'] + 'Feedin to and consumption from national grid at the same time. '})

        return

    def gridavailability_feedin(oemof_results, e_flows_df):

        if (('Consumption from main grid' in e_flows_df.columns)
                and ('Feed into main grid' in e_flows_df.columns)):

            boolean = True

            if any(e_flows_df['Feed into main grid'] != 0 and e_flows_df['Grid availability'] == 0):
                boolean = False

            if boolean == False:
                logging.warning("ATTENTION: Feedin to national grid during blackout!")
                oemof_results.update(
                    {'comments': oemof_results['comments'] + 'Feedin to national grid during blackout. '})

        return

    def gridavailability_consumption(oemof_results, e_flows_df):
        if (('Consumption from main grid' in e_flows_df.columns)
                and ('Grid availability' in e_flows_df.columns)):

            boolean = True

            if any(e_flows_df['Consumption from main grid'] != 0 and e_flows_df['Grid availability'] == 0):
                boolean = False

            if boolean == False:
                logging.warning("ATTENTION: Consumption from national grid during blackout!")
                oemof_results.update(
                    {'comments': oemof_results['comments'] + 'Consumption from national grid during blackout. '})

        return

    def excess_shortage(oemof_results, e_flows_df):
        if (('Excess electricity' in e_flows_df.columns)
                and ('Demand shortage' in e_flows_df.columns)):

            boolean = True

            if any(e_flows_df['Excess electricity'] != 0 and e_flows_df['Demand shortage'] != 0):
                boolean = False

            if boolean == False:
                logging.warning("ATTENTION: Excess and shortage at the same time!")
                oemof_results.update(
                    {'comments': oemof_results['comments'] + 'Excess and shortage at the same time. '})

        return


    def excess_feedin(oemof_results, e_flows_df):
        if (('Excess electricity' in e_flows_df.columns)
                and ('Grid availability' in e_flows_df.columns)
                and ('Feed into main grid' in e_flows_df.columns)):

            boolean = True

            if any(
                    ((e_flows_df['Excess electricity'] != 0)
                     and (e_flows_df['Feed into main grid'] != oemof_results['capacity pcc'])) # actual name!
                    or
                    ((e_flows_df['Excess electricity'] != 0) and (e_flows_df['Grid availability'] == 0))):
                boolean = False

            if boolean == False:
                logging.warning("ATTENTION: Feedin to national grid during blackout!")
                oemof_results.update(
                    {'comments': oemof_results['comments'] + 'Feedin to national grid during blackout. '})

        return


------------------------------------------------------
"""
Requires:
oemof, matplotlib, demandlib, pvlib
tables, tkinter
"""

###############################################################################
# Imports and initialize
###############################################################################

# from oemof.tools import helpers
import pprint as pp
import pandas as pd
import oemof.solph as solph
import oemof.outputlib as outputlib
import logging

import constraints_custom as constraints

# Try to import matplotlib librar
try:
    import matplotlib.pyplot as plt
except ImportError:
    logging.warning('Attention! matplotlib could not be imported.')
    plt = None

###############################################################################
# Define all oemof_functioncalls (including generate graph etc)
###############################################################################
class add_results():


    ######## Processing ########
    def process_basic(micro_grid_system, case_dict, experiment, demand_profile):
        # define an alias for shorter calls below (optional)
        results = micro_grid_system.results['main']
        meta = micro_grid_system.results['meta']

        #get all from node electricity bus
        electricity_bus = outputlib.views.node(results, 'bus_electricity_mg')
        fuel_bus = outputlib.views.node(results, 'bus_fuel')
        oemof_process.outputs_bus_electricity_mg(case_dict, electricity_bus, experiment['filename'])

        # get all from node storage
        if case_dict['storage_fixed_capacity'] != None:
            generic_storage = outputlib.views.node(results, 'generic_storage')
            oemof_process.outputs_storage(generic_storage, case_dict['case_name'], experiment['filename'])
        else:
            generic_storage = None

        oemof_process.print_oemof_meta_main_invest(meta, electricity_bus, case_dict['case_name'])

        total_demand_kWh = sum(demand_profile)

        if case_dict['genset_fixed_capacity'] != None:
            total_fuel_consumption_l = fuel_bus['sequences'][(('source_fuel', 'bus_fuel'), 'flow')].sum()
            total_genset_generation_kWh = electricity_bus['sequences'][
                (('transformer_fuel_generator', 'bus_electricity_mg'), 'flow')].sum()
        else:
            total_fuel_consumption_l = 0
            total_genset_generation_kWh = 0


        if case_dict['pv_fixed_capacity'] != None:
            total_pv_generation_kWh = electricity_bus['sequences'][(('source_pv', 'bus_electricity_mg'), 'flow')].sum()
        else:
            total_pv_generation_kWh = 0


        # As in to storage
        if case_dict['storage_fixed_capacity'] != None:
            total_battery_throughput_kWh = electricity_bus['sequences'][(('bus_electricity_mg', 'generic_storage'), 'flow')].sum()
        else:
            total_battery_throughput_kWh = 0

        # shortage
        if case_dict['allow_shortage'] == True:
            total_shortage_kWh = electricity_bus['sequences'][(('source_shortage', 'bus_electricity_mg'), 'flow')].sum()
        else:
            total_shortage_kWh = 0

        total_supplied_demand_kWh = total_demand_kWh - total_shortage_kWh
        # todo: if freq=15 min, this has to be adjusted!

        from config import evaluated_days
        process.annual_value(total_demand_kWh, evaluated_days)
        process.annual_value(total_supplied_demand_kWh, evaluated_days)
        process.annual_value(total_fuel_consumption_l, evaluated_days)
        process.annual_value(total_genset_generation_kWh, evaluated_days)
        process.annual_value(total_pv_generation_kWh, evaluated_days)
        process.annual_value(total_battery_throughput_kWh, evaluated_days)
        process.annual_value(total_shortage_kWh, evaluated_days)

        # Defining oemof_results (first entries).
        # Added in main_tool: 'grid_reliability', 'grid_total_blackout_duration', 'grid_number_of_blackouts' (only for cases)
        # Specific values added in process_fix/process_oem
        oemof_results = {
            'case':                         case_dict['case_name'],
            'filename':                     'results_' + case_dict['case_name'] + experiment['filename'],
            'consumption_fuel_annual_l':    total_fuel_consumption_l,
            'total_demand_annual_kWh':      total_demand_kWh,
            'total_demand_supplied_annual_kWh': total_supplied_demand_kWh,
            'total_demand_shortage_annual_kWh': total_shortage_kWh,
            'supply_reliability':           total_supplied_demand_kWh/total_demand_kWh,
            'demand_peak_kW':               max(demand_profile),
            'total_genset_generation_kWh':  total_genset_generation_kWh,
            'total_pv_generation_kWh':      total_pv_generation_kWh,
            'total_battery_throughput_kWh': total_battery_throughput_kWh,
            'objective_value':              meta['objective'],
            'comments':                     ''
             }

        #todo change or describe where costs and revenues are generated at main grid interconenection
        # payments always for kWh FROM SIDE OF MAIN GRID
        total_pcoupling_throughput_kWh = 0
        total_fossil_supply = total_genset_generation_kWh
        if case_dict['pcc_consumption_fixed_capacity'] != None or case_dict['pcc_feedin_fixed_capacity'] != None:
            maingrid_bus = outputlib.views.node(results, 'bus_electricity_ng')
            if case_dict['pcc_consumption_fixed_capacity'] != None:
                print(maingrid_bus['sequences'][(('bus_electricity_ng', 'transformer_pcc_consumption'), 'flow')])
                # attention! this is from side of main grid!
                consumption_main_grid_no_inv_loss =  maingrid_bus['sequences'][(('bus_electricity_ng', 'transformer_pcc_consumption'), 'flow')].sum()\
                # attention: only effectively used electricity consumption counts for renewable share
                consumption_main_grid_inv_loss = electricity_bus['sequences'][(('transformer_pcc_consumption', 'bus_electricity_mg'), 'flow')].sum()
                process.annual_value(consumption_main_grid_no_inv_loss, evaluated_days)
                process.annual_value(consumption_main_grid_inv_loss, evaluated_days)

                oemof_results.update({'consumption_main_grid_annual_kWh': consumption_main_grid_no_inv_loss})
                # attention: only effectively used electricity consumption counts for renewable share
                total_pcoupling_throughput_kWh += oemof_results['consumption_main_grid_annual_kWh'] # payments also for inverter loss
                total_fossil_supply +=  consumption_main_grid_inv_loss * (1-experiment['maingrid_renewable_share'])

            if case_dict['pcc_feedin_fixed_capacity'] != None:
                feedin_main_grid_inv_loss  = maingrid_bus['sequences'][(('transformer_pcc_feedin', 'bus_electricity_ng'), 'flow')].sum()
                                          # feed in only enumerated after lossy transformer
                process.annual_value(feedin_main_grid_inv_loss, evaluated_days)
                oemof_results.update({'feedin_main_grid_annual_kWh': feedin_main_grid_inv_loss})
                total_pcoupling_throughput_kWh += oemof_results['feedin_main_grid_annual_kWh']

        # todo this includes actual fossil share including pcc inefficiencies
        res_share = abs(1 - total_fossil_supply / total_supplied_demand_kWh)

        oemof_results.update({'total_pcoupling_throughput_kWh':   total_pcoupling_throughput_kWh,
                              'res_share': res_share})

        #constraints.renewable_share_test(oemof_results, experiment)

        return results, meta, electricity_bus, oemof_results, generic_storage

    def process_fix(micro_grid_system, case_dict, experiment, capacity_batch, demand_profile):
        from config import include_stability_constraint
        # todo: this might be possible to do a bit shorter
        results, meta, electricity_bus, oemof_results, generic_storage = oemof_process.process_basic(micro_grid_system, case_dict, experiment, demand_profile)

        oemof_results = add_results.project_annuities(case_dict, oemof_results, experiment, capacity_batch)

        logging.info('    Dispatch optimization for case "' + case_dict['case_name'] + '" finished, with renewable share of ' +
                     str(round(oemof_results['res_share']*100,2)) + ' percent.'
                      + ' with a reliability of '+ str(round(oemof_results['supply_reliability']*100,2)) + ' percent')

        if case_dict['storage_fixed_capacity'] != None:
            storage_capacity = generic_storage['sequences'][(('generic_storage', 'None'), 'capacity')]
        else:
            storage_capacity = pd.Series([0 for t in demand_profile.index], index=demand_profile.index)

        #if include_stability_constraint == True:
            #constraints.stability_test(oemof_results, experiment, storage_capacity, demand_profile,
                                                 #genset_capacity = capacity_batch['capacity_genset_kW'])

        return oemof_results

    def process_oem(micro_grid_system, case_dict, pv_generation_max, experiment, demand_profile):
        from config import include_stability_constraint

        results, meta, electricity_bus, oemof_results, generic_storage = oemof_process.process_basic(micro_grid_system, case_dict, experiment, demand_profile)

        capacities_base = {}
        # --------------pv capacity -------------#
        if case_dict['pv_fixed_capacity'] == False:
            if pv_generation_max > 1:
                capacities_base.update({'capacity_pv_kWp': electricity_bus['scalars'][(('source_pv', 'bus_electricity_mg'), 'invest')]* pv_generation_max })
            elif pv_generation_max > 0 and pv_generation_max < 1:
                capacities_base.update({'capacity_pv_kWp': electricity_bus['scalars'][(('source_pv', 'bus_electricity_mg'), 'invest')] / pv_generation_max })
            else:
                logging.warning("Error, Strange PV behaviour (PV gen < 0)")
        elif isinstance(case_dict['pv_fixed_capacity'], float):
                capacities_base.update({'capacity_pv_kWp': case_dict['pv_fixed_capacity']})
        elif case_dict['pv_fixed_capacity'] == None:
            capacities_base.update({'capacity_pv_kWp': 0})

        # --------------genset capacity -------------#
        if case_dict['genset_fixed_capacity'] == False:
            # Optimized generator capacity
            capacities_base.update({'capacity_genset_kW': electricity_bus['scalars'][(('transformer_fuel_generator', 'bus_electricity_mg'), 'invest')]})
        elif isinstance(case_dict['genset_fixed_capacity'], float):
            capacities_base.update({'capacity_genset_kW': case_dict['genset_fixed_capacity']})
        elif case_dict['genset_fixed_capacity']==None:
            capacities_base.update({'capacity_genset_kW': 0})

        # --------------storage capacity -------------#
            # print(electricity_bus['scalars'][(('bus_electricity_mg', 'generic_storage'), 'invest')])
            # print(electricity_bus['scalars'][(('generic_storage', 'bus_electricity_mg'), 'invest')])
            # print(electricity_bus['scalars'][(('generic_storage', None), 'invest')])

        if case_dict['storage_fixed_capacity'] == False:
        # Optimized generator capacity
            capacity_battery = electricity_bus['scalars'][(('bus_electricity_mg', 'generic_storage'), 'invest')]/experiment['storage_Crate_charge']
            # possibly using generic_storage['scalars'][((generic_storage, None), invest)]
            capacities_base.update({'capacity_storage_kWh': capacity_battery})
        elif isinstance(case_dict['storage_fixed_capacity'], float):
            capacities_base.update({'capacity_storage_kWh': case_dict['storage_fixed_capacity']})
        elif case_dict['storage_fixed_capacity'] == None:
            capacities_base.update({'capacity_storage_kWh': 0})

        # --------------pcc capacity -------------#
        if case_dict['pcc_consumption_fixed_capacity'] != None or case_dict['pcc_feedin_fixed_capacity'] != None:
            pcc_cap = []
            maingrid_bus = outputlib.views.node(results, 'bus_electricity_ng')
            if case_dict['pcc_consumption_fixed_capacity'] == False:
                pcc_cap.append(maingrid_bus['sequences'][(('bus_electricity_ng', 'transformer_pcc_consumption'), 'flow')].max())
            elif isinstance(case_dict['pcc_consumption_fixed_capacity'], float):
                pcc_cap.append(case_dict['pcc_consumption_fixed_capacity'])

            if case_dict['pcc_feedin_fixed_capacity'] == False:
                pcc_cap.append(max(maingrid_bus['sequences'][(('transformer_pcc_feedin', 'bus_electricity_ng'), 'flow')]))
            elif isinstance(case_dict['pcc_feedin_fixed_capacity'], float):
                pcc_cap.append(case_dict['pcc_feedin_fixed_capacity'])
            capacities_base.update({'capacity_pcoupling_kW': max(pcc_cap)})
        elif case_dict['pcc_consumption_fixed_capacity'] == None and case_dict['pcc_feedin_fixed_capacity'] == None:
            capacities_base.update({'capacity_pcoupling_kW': 0})

        oemof_results = add_results.project_annuities(case_dict, oemof_results, experiment, capacities_base)

        logging.info ('    Exact OEM results of case "' + case_dict['case_name'] + '" : \n'
                      +'    '+'  '+ '    ' + '    ' + '    ' + str(round(capacities_base['capacity_storage_kWh'],3)) + ' kWh battery, '
                      + str(round(capacities_base['capacity_pv_kWp'],3)) + ' kWp PV, '
                      + str(round(capacities_base['capacity_genset_kW'],3)) + ' kW genset '
                      + 'at a renewable share of ' + str(round(oemof_results['res_share']*100,2)) + ' percent'
                      + ' with a reliability of '+ str(round(oemof_results['supply_reliability']*100,2)) + ' percent')

        if case_dict['storage_fixed_capacity'] != None:
            storage_capacity = generic_storage['sequences'][(('generic_storage', 'None'), 'capacity')]
        else:
            storage_capacity = [0 for t in range(0, len(demand_profile.index))]

        #if include_stability_constraint == True:
            #constraints.stability_test(oemof_results, experiment, storage_capacity, demand_profile,
                                        #genset_capacity = capacities_base['capacity_genset_kW'])

        return oemof_results, capacities_base

    def process_oem_batch(capacities_base, case_name):
        from input_values import round_to_batch
        capacities_base.update({'capacity_pv_kWp': round (0.5+capacities_base['capacity_pv_kWp']/round_to_batch['PV'])
                                                  *round_to_batch['PV']}) # immer eher 0.25 capacity mehr als eigentlich nötig
        capacities_base.update({'capacity_genset_kW': round(0.5+capacities_base['capacity_genset_kW'] / round_to_batch['GenSet']) *
                                                  round_to_batch['GenSet']})
        capacities_base.update({'capacity_storage_kWh': round(0.5+capacities_base['capacity_storage_kWh'] / round_to_batch['Storage']) *
                                                  round_to_batch['Storage']})
        capacities_base.update(
            {'capacity_pcoupling_kW': round(0.5 + capacities_base['capacity_pcoupling_kW'] / round_to_batch['Pcoupling']) *
                                     round_to_batch['Pcoupling']})
        logging.debug ('    Equivalent batch capacities of base OEM for dispatch OEM in case "' + case_name + '": \n'
                      + '    ' + '  ' + '    ' + '    ' + '    ' + str(capacities_base['capacity_storage_kWh']) + ' kWh battery, '
                      + str(capacities_base['capacity_pv_kWp']) + ' kWp PV, '
                      + str(capacities_base['capacity_genset_kW']) + ' kW genset.')
        return capacities_base


    ######## Processing ########

    ####### Show #######
    def outputs_storage(custom_storage, case_name, filename):
        from config import display_graphs_flows_storage, setting_save_flows_storage
        if display_graphs_flows_storage == True or setting_save_flows_storage == True:
            stored_capacity = custom_storage['sequences'][(('generic_storage', 'None'), 'capacity')]
            discharge       = custom_storage['sequences'][(('generic_storage', 'bus_electricity_mg'), 'flow')]
            charge          = custom_storage['sequences'][(('bus_electricity_mg', 'generic_storage'), 'flow')]

        if setting_save_flows_storage == True:
            from config import output_folder
            storage_flows = pd.DataFrame(stored_capacity.values, columns=['Stored capacity in kWh'], index=stored_capacity.index)
            storage_flows = storage_flows.join(
                pd.DataFrame(discharge.values, columns=['Discharge storage'], index=discharge.index))
            storage_flows = storage_flows.join(
                pd.DataFrame(charge.values, columns=['Charge storage'], index=charge.index))

            storage_flows.to_csv(output_folder  +   '/storage/' + case_name + filename + '_storage.csv')

        if plt is not None and display_graphs_flows_storage == True:
            logging.debug('Plotting: Generic storage')
            stored_capacity.plot(kind='line', drawstyle='steps-post', label='Stored capacity in kWh')
            discharge.plot(kind='line', drawstyle='steps-post', label='Discharge storage')
            charge.plot(kind='line', drawstyle='steps-post', label='Charge storage')
            plt.legend(loc='upper right')
            plt.show()
        return