"""
Requires:
oemof, matplotlib, demandlib, pvlib
tables, tkinter
"""

# from oemof.tools import helpers
#import pprint as pp
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

class evaluate_timeseries:
    '''
    All functions to extract timeseries from oemof results.
    Main function called from XY: evaluate_timeseries.get_all
    All other functions are called by evaluate_timeseries.get_all itself
    '''
    def get_all(case_dict, micro_grid_system, experiment, grid_availability, pv_generation_max):
        from config import date_time_index
        '''
        Main function called from XY.
        Funktion to extract simulation results from oemof result file,
        including extraction of time series, accumulated values, optimized capacities.
        Simulation results are extracted based on their case definitions in case_dict,
        thus the only part where changes are neccesary to modify cases is not here but
        in the case definitions directly (oemof_cases). If the computation of the extracted
        results itself should change (eg. in the future allowing a finer timestep resulution),
        this is the right place.

        :param case_dict: Case specific definitions, indicating used oemof objects
        :param micro_grid_system: simulation results as provided by oemof
        :param experiment: experiment parameters as defined in input_values
        :param grid_availability: grid_availability timeseries
                (could also be extracted from micro_grid_system as actual value of national grid source / sink)
        :return: oemof_results for proceeding saving in excel file, e_bus_flows
        # todo actually, it would not be needed to write to csv file externally, e_bus_flows not needed at all later on?
        '''

        results = micro_grid_system.results['main']
        meta = micro_grid_system.results['meta']

        oemof_results = {
            'case': case_dict['case_name'],
            'filename': 'results_' + case_dict['case_name'] + experiment['filename'],
            'objective_value': meta['objective'],
            'comments': ''
        }

        # get all from node electricity bus
        electricity_bus = outputlib.views.node(results, 'bus_electricity_mg')
        e_flows_df = timeseries.get_demand(case_dict, oemof_results, electricity_bus)
        e_flows_df = timeseries.get_shortage(case_dict, oemof_results, electricity_bus, e_flows_df)
        # todo specify reliability into supply_reliability_kWh, national_grid_reliability_h
        oemof_results.update({'supply_reliability':
                                  oemof_results['total_demand_supplied_annual_kWh'] / oemof_results[
                                      'total_demand_annual_kWh']})

        e_flows_df = timeseries.get_excess(case_dict, oemof_results, electricity_bus, e_flows_df)
        e_flows_df = timeseries.get_pv(case_dict, oemof_results, electricity_bus, e_flows_df, pv_generation_max)
        e_flows_df = timeseries.get_genset(case_dict, oemof_results, electricity_bus, e_flows_df)
        e_flows_df = timeseries.get_storage(case_dict, oemof_results, experiment, results, e_flows_df)
        timeseries.get_fuel(case_dict, oemof_results, results)
        e_flows_df = timeseries.get_shortage(case_dict, oemof_results, results, e_flows_df)

        # todo still decide with of the flows to include in e_flow_df, and which ones to put into oemof results for cost calculation (expenditures, revenues)
        e_flows_df = timeseries.get_national_grid(case_dict, oemof_results, results, e_flows_df, grid_availability)
        timeseries.get_res_share(case_dict, oemof_results, experiment)
        plausability_tests.run(oemof_results, e_flows_df)

        # todo this is not jet implemented!
        constraints.stability_test(oemof_results, experiment, e_flows_df)

        # todo this has to be at end using e_flows_df, has to be edited
        #oemof_process.outputs_bus_electricity_mg(case_dict, electricity_bus, experiment['filename'])
        # oemof_process.outputs_storage(generic_storage, case_dict['case_name'], experiment['filename'])

        from oemof_process_results import oemof_process
        oemof_process.print_oemof_meta_main_invest(meta, electricity_bus, case_dict['case_name'])

        ## todo  why is that even necessary?? i could define base_capacities directly in oemof_results. check
        # if directly defined, wich would be nice, then even with no grid connection value cap_pcc = 0 is added, instead on no value at all
        # currently, that is done anyway...
        #oemof_results = add_results.project_annuities(case_dict, oemof_results, experiment, capacities_base)

        # id like it more if res share, supply reliability and lcoe were displayed at once

        logging.info ('    Exact OEM results of case "' + case_dict['case_name'] + '" : \n'
                      +'    '+'  '+ '    ' + '    ' + '    ' + str(round(oemof_results['capacity_storage_kWh'],3)) + ' kWh battery, '
                      + str(round(oemof_results['capacity_pv_kWp'],3)) + ' kWp PV, '
                      + str(round(oemof_results['capacity_genset_kW'],3)) + ' kW genset '
                      + 'at a renewable share of ' + str(round(oemof_results['res_share']*100,2)) + ' percent'
                      + ' with a reliability of '+ str(round(oemof_results['supply_reliability']*100,2)) + ' percent')


        return oemof_results

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
        return e_flows_df

    def get_excess(case_dict, oemof_results, electricity_bus, e_flows_df):
        # Get flow
        excess = electricity_bus['sequences'][(('bus_electricity_mg', 'sink_excess'), 'flow')]
        e_flows_df = utilities.join_e_flows_df(excess, 'Excess generation', e_flows_df)
        utilities.annual_value('total_demand_shortage_annual_kWh', excess, oemof_results, case_dict) # not given as result.csv right now
        return e_flows_df

    def get_pv(case_dict, oemof_results, electricity_bus, e_flows_df, pv_generation_max):
        # Get flow
        if case_dict['pv_fixed_capacity'] != None:
            pv_gen = electricity_bus['sequences'][(('source_pv', 'bus_electricity_mg'), 'flow')]
            utilities.annual_value('total_pv_generation_kWh', pv_gen, oemof_results, case_dict)
            e_flows_df = utilities.join_e_flows_df(pv_gen, 'PV generation', e_flows_df)

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

    def get_genset(case_dict, oemof_results, electricity_bus, e_flows_df):
        # Get flow
        if case_dict['genset_fixed_capacity'] != None:
            genset = electricity_bus['sequences'][(('transformer_fuel_generator', 'bus_electricity_mg'), 'flow')]
            utilities.annual_value('total_genset_generation_kWh', genset, oemof_results, case_dict)
            e_flows_df = utilities.join_e_flows_df(genset, 'Genset generation', e_flows_df)

        # Get capacity
        if case_dict['genset_fixed_capacity'] == False:
            # Optimized generator capacity
            oemof_results.update({'capacity_genset_kW': electricity_bus['scalars'][(('transformer_fuel_generator', 'bus_electricity_mg'), 'invest')]})
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

        from config import setting_pcc_utility_owned
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

            consumption_utility_side = national_grid_bus['sequences'][(('electricity_bus_ng', 'transformer_pcc_consumption'), 'flow')]
            e_flows_df = utilities.join_e_flows_df(consumption_utility_side, 'Consumption from main grid (utility side)', e_flows_df)
            utilities.annual_value('consumption_main_grid_utility_side_annual_kWh', consumption_utility_side, oemof_results,
                                   case_dict)
            # todo dependent on from config import setting_pcc_utility_owned either choose first or last for expenditures!
            # if setting_pcc_utility_owned == True:

        if case_dict['pcc_feedin_fixed_capacity'] != None:
            feedin_mg_side = micro_grid_bus['sequences'][(('bus_electricity_mg', 'transformer_pcc_feedin'), 'flow')]
            e_flows_df = utilities.join_e_flows_df(feedin_mg_side, 'Feed into main grid (MG side)', e_flows_df)
            utilities.annual_value('feedin_main_grid_mg_side_annual_kWh', feedin_mg_side, oemof_results, case_dict)

            feedin_utility_side = national_grid_bus['sequences'][(('transformer_pcc_feedin', 'electricity_bus_ng'), 'flow')]
            e_flows_df = utilities.join_e_flows_df(e_flows_df, feedin_utility_side, 'Feed into main grid (utility side)')
            utilities.annual_value('feedin_main_grid_utility_side_annual_kWh', feedin_utility_side, oemof_results, case_dict)

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
        # todo change or describe where costs and revenues are generated at main grid interconenection
        # payments always for kWh FROM SIDE OF MAIN GRID
        total_fossil_supply = 0
        if case_dict['genset_fixed_capacity'] != None:
            total_fossil_supply += oemof_results['total_genset_generation_kWh']
        if case_dict['pcc_consumption_fixed_capacity'] != None:
            # attention: only effectively used electricity consumption counts for renewable share
            total_fossil_supply += oemof_results['consumption_main_grid_mg_side_annual_kWh'] \
                                   * (1 - experiment['maingrid_renewable_share'])

        if case_dict['pcc_feedin_fixed_capacity'] != None:
            total_pcoupling_throughput_kWh += oemof_results['feedin_main_grid_mg_side_annual_kWh']

        # todo this includes actual fossil share including pcc inefficiencies
        res_share = abs(1 - total_fossil_supply / oemof_results['total_demand_supplied_annual_kWh'])

        oemof_results.update({'res_share': res_share})
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
        if ('Storage discharge' in e_flows_df.columns and 'Storage charge' in e_flows_df.columns):
            boolean = True

            test = [(e_flows_df['Storage discharge'][t] != 0 and e_flows_df['Storage charge'][t] == 0) for t in e_flows_df.index]

            if any(test) == False:
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

            test = [(e_flows_df['Demand supplied'] != e_flows_df['Demand'] and e_flows_df['Demand shortage'] == 0) for t in
                    e_flows_df.index]

            if any(test) == False:
                boolean = False

            if boolean == False:
                logging.warning("ATTENTION: Demand not fully supplied but no shortage!")
                oemof_results.update({'comments': oemof_results['comments'] + 'Demand not fully supplied but no shortage. '})

        return


    def feedin_consumption(oemof_results, e_flows_df):
        if (('Consumption from main grid' in e_flows_df.columns)
                and ('Feed into main grid' in e_flows_df.columns)):

            boolean = True

            test = [(e_flows_df['Consumption from main grid'] != 0 and e_flows_df['Feed into main grid'] != 0) for t in
                    e_flows_df.index]

            if any(test) == False:
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

            test = [(e_flows_df['Feed into main grid'] != 0 and e_flows_df['Grid availability'] == 0) for t in
                    e_flows_df.index]

            if any(test) == False:
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

            test = [(e_flows_df['Consumption from main grid'] != 0 and e_flows_df['Grid availability'] == 0) for t in
                    e_flows_df.index]

            if any(test) == False:
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

            test = [(e_flows_df['Excess electricity'] != 0 and e_flows_df['Demand shortage'] != 0) for t in
                    e_flows_df.index]

            if any(test) == False:
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

            test = [(((e_flows_df['Excess electricity'] != 0) and (e_flows_df['Feed into main grid'] != oemof_results['capacity pcc'])) # actual name!
                    or
                    ((e_flows_df['Excess electricity'] != 0) and (e_flows_df['Grid availability'] == 0)))
                    for t in e_flows_df.index]

            if any(test) == False:
                boolean = False

            if boolean == False:
                logging.warning("ATTENTION: Feedin to national grid during blackout!")
                oemof_results.update(
                    {'comments': oemof_results['comments'] + 'Feedin to national grid during blackout. '})

        return

###############################################################################
# Define all oemof_functioncalls (including generate graph etc)
###############################################################################
class add_results():

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
    def outputs_mg_flows(case_dict, e_flows_df):
        from config import display_graphs_flows_electricity_mg, setting_save_flows_storage
        #insert pandas plot here
        return

    def outputs_storage(case_dict, e_flows_df):
        if case_dict['storage_fixed_capacity'] != None:
            from config import display_graphs_flows_storage, setting_save_flows_storage
            storage_flows = pd.DataFrame([e_flows_df['Storage charge'], e_flows_df['Storage discharge'], e_flows_df['Stored capacity']])
            if setting_save_flows_storage == True:
                from config import output_folder
                storage_flows.to_csv(output_folder + '/storage/' + case_name + filename + '_storage.csv')

                storage_flows.plot(title='Operation of storage')
                plt.show()
        # insert pandas plot here
        return

    def outputs_ng_flows(case_dict, e_flows_df):
        return


    def outputs_storage(custom_storage, case_name, filename):
        from config import display_graphs_flows_storage, setting_save_flows_storage
        if display_graphs_flows_storage == True or setting_save_flows_storage == True:
            storage_flows = pd.DataFrame(stored_capacity.values, columns=['Stored capacity in kWh'], index=stored_capacity.index)
            storage_flows = storage_flows.join(
                pd.DataFrame(discharge.values, columns=['Discharge storage'], index=discharge.index))
            storage_flows = storage_flows.join(
                pd.DataFrame(charge.values, columns=['Charge storage'], index=charge.index))

        if setting_save_flows_storage == True:
            from config import output_folder
            storage_flows.to_csv(output_folder  +   '/storage/' + case_name + filename + '_storage.csv')

        if display_graphs_flows_storage == True:
            pass

        return