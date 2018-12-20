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

    def project_annuities(case_dict, oemof_results, experiment, capacities):
        from config import evaluated_days

        # Define all capacities of the case
        # (capacity_pv_kWp, capacity_storage_kWh, capacity_genset_kW, capacity_pcoupling_kW)
        oemof_results = add_results.capacities(case_dict, oemof_results, capacities)

        # Define all annuities based on component capacities (Capex+Opex), add var. operational costs
        # Extrapolate to costs of whole year
        oemof_results = add_results.annuities_365(case_dict, oemof_results, experiment, capacities, evaluated_days)

        # Add costs related to annuities
        oemof_results = add_results.costs(oemof_results, experiment)

        # Expenditures for fuel:
        oemof_results = add_results.expenditures_fuel(oemof_results, experiment)

        if case_dict['pcc_consumption_fixed_capacity'] != None or case_dict['pcc_feedin_fixed_capacity'] != None:
            #---------Expenditures from electricity consumption from main grid ----------#
            oemof_results = add_results.expenditures_main_grid_consumption(oemof_results, experiment)

        if case_dict['pcc_feedin_fixed_capacity'] != None:
            # ---------Revenues from electricity feed-in to main grid ----------#
            oemof_results = add_results.revenue_main_grid_feedin(oemof_results, experiment)

        oemof_results.update({
            'npv': oemof_results['annuity'] * experiment['annuity_factor'],
            'lcoe': oemof_results['annuity'] / oemof_results['demand_annual_supplied_kWh']
        })

        # todo: this does not inlude costs for unsupplied demand!
        return oemof_results

    def capacities(case_dict, oemof_results, capacities):
        oemof_results.update({'capacity_pv_kWp': capacities['capacity_pv_kWp']})
        oemof_results.update({'capacity_storage_kWh': capacities['capacity_storage_kWh']})
        oemof_results.update({'capacity_genset_kW': capacities['capacity_genset_kW']})
        oemof_results.update({'capacity_pcoupling_kW': capacities['capacity_pcoupling_kW']})
        return oemof_results

    def annuities_365(case_dict, oemof_results, experiment, capacities, evaluated_days):

        interval_annuity={
            'annuity_pv': experiment['pv_cost_annuity'] * capacities['capacity_pv_kWp'],
            'annuity_storage': experiment['storage_cost_annuity'] * capacities['capacity_storage_kWh'],
            'annuity_genset': experiment['genset_cost_annuity'] * capacities['capacity_genset_kW'],
            'annuity_pcoupling': experiment['pcoupling_cost_annuity'] * capacities['capacity_pcoupling_kW'] ,
            'annuity_project': experiment['project_cost_annuity'],
            'annuity_distribution_grid': experiment['distribution_grid_cost_annuity']}

        # Main grid extension
        if case_dict['pcc_consumption_fixed_capacity'] != None or case_dict['pcc_feedin_fixed_capacity'] != None:
            interval_annuity.update({
                'annuity_grid_extension':
                    experiment['maingrid_extension_cost_annuity'] * experiment['maingrid_distance']})
        else:
            interval_annuity.update({'annuity_grid_extension': 0})

        om_var_interval={
            'om_var_pv': oemof_results['total_pv_generation_kWh']*experiment['pv_cost_var'],
            'om_var_storage': oemof_results['total_battery_throughput_kWh']*experiment['storage_cost_var'],
            'om_var_genset': oemof_results['total_genset_generation_kWh']*experiment['genset_cost_var'],
            'om_var_pcoupling': oemof_results['total_pcoupling_throughput_kWh']*experiment['pcoupling_cost_var']
        }

        oemof_results.update({
            'annuity_pv':
                (interval_annuity['annuity_pv'] + om_var_interval['om_var_pv'])* 365 / evaluated_days,
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
                                         + oemof_results['annuity_storage']
                                         + oemof_results['annuity_genset']
                                         + oemof_results['annuity_pcoupling']
                                         + oemof_results['annuity_project']
                                         + oemof_results['annuity_distribution_grid']
                                         + oemof_results['annuity_grid_extension']})

        return oemof_results

    def costs(oemof_results, experiment):
        oemof_results.update({
            'costs_pv': oemof_results['annuity_pv'] * experiment['annuity_factor'],
            'costs_storage': oemof_results['annuity_storage'] * experiment['annuity_factor'],
            'costs_genset': oemof_results['annuity_genset'] * experiment['annuity_factor'],
            'costs_pcoupling': oemof_results['annuity_pcoupling'] * experiment['annuity_factor'],
            'costs_project': oemof_results['annuity_project'] * experiment['annuity_factor'],
            'costs_distribution_grid': oemof_results['annuity_distribution_grid'] * experiment['annuity_factor'],
            'costs_grid_extension': oemof_results['annuity_grid_extension'] * experiment['annuity_factor']
        })
        return oemof_results

    def expenditures_fuel(oemof_results, experiment):
        # Necessary in oemof_results: consumption_main_grid_annual
        oemof_results.update({'expenditures_fuel_annual':
                oemof_results['consumption_fuel_annual_l'] * experiment['price_fuel'] / experiment['combustion_value_fuel']})

        oemof_results.update({'expenditures_fuel_total':
                oemof_results['expenditures_fuel_annual'] * experiment['annuity_factor']})

        oemof_results.update({'annuity': oemof_results['annuity'] + oemof_results['expenditures_fuel_annual']})
        return oemof_results

    def expenditures_main_grid_consumption(oemof_results, experiment):
        # Necessary in oemof_results: consumption_main_grid_annual
        oemof_results.update({'expenditures_main_grid_consumption_annual':
                oemof_results['consumption_main_grid_annual_kWh'] * experiment['maingrid_electricity_price']})

        oemof_results.update({'expenditures_main_grid_consumption_total':
                oemof_results['expenditures_main_grid_consumption_annual'] * experiment['annuity_factor']})

        oemof_results.update({'annuity': oemof_results['annuity'] + oemof_results['expenditures_main_grid_consumption_annual']})
        return oemof_results

    # todo include above
    def expenditures_shortage(oemof_results, experiment):
        # Necessary in oemof_results: consumption_main_grid_annual
        oemof_results.update({'expenditures_shortage_annual':
                - oemof_results['demand_shortage_annual_kWh'] * experiment['costs_var_unsupplied_load']})

        oemof_results.update({'expenditures_shortage_total':
                oemof_results['expenditures_shortage_annual'] * experiment['annuity_factor']})

        oemof_results.update({'annuity': oemof_results['annuity'] + oemof_results['expenditures_shortage_annual']})
        return oemof_results

    def revenue_main_grid_feedin(oemof_results, experiment):
        # Necessary in oemof_results: feedin_main_grid_annual
        oemof_results.update({'revenue_main_grid_feedin_annual':
                - oemof_results['feedin_main_grid_annual_kWh'] * experiment['maingrid_feedin_tariff']})

        oemof_results.update({'revenue_main_grid_feedin_total':
                oemof_results['revenue_main_grid_feedin_annual'] * experiment['annuity_factor']})

        oemof_results.update(
            {'annuity': oemof_results['annuity'] + oemof_results['revenue_main_grid_feedin_annual']})
        return oemof_results

class oemof_process():

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

        total_demand = sum(demand_profile)

        if case_dict['genset_fixed_capacity'] != None:
            total_fuel_consumption = fuel_bus['sequences'][(('source_fuel', 'bus_fuel'), 'flow')].sum()
            total_genset_generation_kWh = electricity_bus['sequences'][
                (('transformer_fuel_generator', 'bus_electricity_mg'), 'flow')].sum()
        else:
            total_fuel_consumption = 0
            total_genset_generation_kWh = 0


        if case_dict['pv_fixed_capacity'] != None:
            total_pv_generation_kWh = electricity_bus['sequences'][(('source_pv', 'bus_electricity_mg'), 'flow')].sum()
        else:
            total_pv_generation_kWh = 0

        total_supplied_demand = electricity_bus['sequences'][(('bus_electricity_mg', 'sink_demand'), 'flow')].sum()

        # As in to storage
        if case_dict['storage_fixed_capacity'] != None:
            total_battery_throughput_kWh = electricity_bus['sequences'][(('bus_electricity_mg', 'generic_storage'), 'flow')].sum()
        else:
            total_battery_throughput_kWh = 0

        from config import evaluated_days
        # todo: if freq=15 min, this has to be adjusted!
        for item in [total_demand,
                     total_supplied_demand,
                     total_fuel_consumption,
                     total_genset_generation_kWh,
                     total_pv_generation_kWh,
                     total_battery_throughput_kWh]:
            item = item * 365 / evaluated_days

        # Defining oemof_results (first entries).
        # Added in main_tool: 'grid_reliability', 'grid_total_blackout_duration', 'grid_number_of_blackouts' (only for cases)
        # Specific values added in process_fix/process_oem
        oemof_results = {
            'case':                         case_dict['case_name'],
            'filename':                     'results_' + case_dict['case_name'] + experiment['filename'],
            'consumption_fuel_annual_l':    total_fuel_consumption,
            'demand_annual_supplied_kWh':   total_supplied_demand,
            'total_demand_annual_kWh':      total_demand,
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
                # attention! this is from side of main grid!
                oemof_results.update({'consumption_main_grid_annual_kWh':
                                          sum(maingrid_bus['sequences'][(('bus_electricity_ng', 'transformer_pcc_consumption'), 'flow')])
                                          * 365 / evaluated_days})
                total_pcoupling_throughput_kWh += oemof_results['consumption_main_grid_annual_kWh']
                # attention: only effectively used electricity consumption counts for renewable share
                total_fossil_supply += electricity_bus['sequences'][(('transformer_pcc_consumption', 'bus_electricity_mg'), 'flow')].sum() \
                                       * 365 / evaluated_days \
                                       * (1-experiment['maingrid_renewable_share'])
            if case_dict['pcc_feedin_fixed_capacity'] != None:
                oemof_results.update({'feedin_main_grid_annual_kWh':
                                          sum(maingrid_bus['sequences'][(('transformer_pcc_feedin', 'bus_electricity_ng'), 'flow')])
                                          * 365 / evaluated_days})
                total_pcoupling_throughput_kWh += oemof_results['feedin_main_grid_annual_kWh']

        # todo this includes actual fossil share including pcc inefficiencies
        res_share = abs(1 - total_fossil_supply / total_supplied_demand)


        oemof_results.update({'total_pcoupling_throughput_kWh':   total_pcoupling_throughput_kWh,
                              'res_share': res_share})

        constraints.renewable_share_test(oemof_results, experiment)

        return results, meta, electricity_bus, oemof_results, generic_storage

    def process_fix(micro_grid_system, case_dict, experiment, capacity_batch, demand_profile):
        from config import include_stability_constraint
        # todo: this might be possible to do a bit shorter
        results, meta, electricity_bus, oemof_results, generic_storage = oemof_process.process_basic(micro_grid_system, case_dict, experiment, demand_profile)

        oemof_results = add_results.project_annuities(case_dict, oemof_results, experiment, capacity_batch)

        logging.info('    Dispatch optimization for case "' + case_dict['case_name'] + '" finished, with renewable share of ' +
                     str(round(oemof_results['res_share']*100,2)) + ' percent.')

        if case_dict['storage_fixed_capacity'] != None:
            storage_capacity = generic_storage['sequences'][(('generic_storage', 'None'), 'capacity')]
        else:
            storage_capacity = pd.Series([0 for t in demand_profile.index], index=demand_profile.index)

        if include_stability_constraint == True:
            constraints.stability_test(oemof_results, experiment, storage_capacity, demand_profile,
                                                 genset_capacity = capacity_batch['capacity_genset_kW'])

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
                      + 'at a renewable share of ' + str(round(oemof_results['res_share']*100,2)) + ' percent.')

        if case_dict['storage_fixed_capacity'] != None:
            storage_capacity = generic_storage['sequences'][(('generic_storage', 'None'), 'capacity')]
        else:
            storage_capacity = [0 for t in range(0, len(demand_profile.index))]

        if include_stability_constraint == True:
            constraints.stability_test(oemof_results, experiment, storage_capacity, demand_profile,
                                        genset_capacity = capacities_base['capacity_genset_kW'])

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

    def print_oemof_meta_main_invest(meta, electricity_bus, case_name):
        # print the solver results
        from config import print_simulation_meta, print_simulation_main, print_simulation_invest

        if print_simulation_meta == True:
            logging.info('********* Meta results *********')
            pp.pprint(meta)

        # print the sums of the flows around the electricity bus
        if print_simulation_main == True:
            logging.info('********* Main results *********')
            pp.pprint(electricity_bus['sequences'].sum(axis=0))

        # print the scalars of investment optimization (not equal to capacities!)
        if case_name == "base_oem" or case_name == "base_oem_with_min_loading":
            if print_simulation_invest == True:
                logging.info('********* Invest results *********')
                pp.pprint(electricity_bus['scalars'])
        return
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

    def outputs_bus_electricity_mg(case_dict, electricity_bus, filename):
        from config import display_graphs_flows_electricity_mg, setting_save_flows_electricity_mg
        # todo actually not quite true here
        if display_graphs_flows_electricity_mg == True or setting_save_flows_electricity_mg == True:
            excess = electricity_bus['sequences'][(('bus_electricity_mg', 'sink_excess'), 'flow')]
            demand_supply = electricity_bus['sequences'][(('bus_electricity_mg', 'sink_demand'), 'flow')]

            if case_dict['pv_fixed_capacity'] != None:
                pv_gen          = electricity_bus['sequences'][(('source_pv', 'bus_electricity_mg'), 'flow')]
            if case_dict['genset_fixed_capacity'] != None:
                genset          = electricity_bus['sequences'][(('transformer_fuel_generator', 'bus_electricity_mg'), 'flow')]
            if case_dict['storage_fixed_capacity'] != None:
                discharge       = electricity_bus['sequences'][(('generic_storage', 'bus_electricity_mg'), 'flow')]
                charge          = electricity_bus['sequences'][(('bus_electricity_mg', 'generic_storage'), 'flow')]

            if case_dict['allow_shortage'] == True:
                shortage = electricity_bus['sequences'][(('source_shortage', 'bus_electricity_mg'), 'flow')]

            if case_dict['pcc_consumption_fixed_capacity'] != None:
                consumption = electricity_bus['sequences'][(('transformer_pcc_consumption', 'bus_electricity_mg'), 'flow')]

            if case_dict['pcc_feedin_fixed_capacity'] != None:
                feedin = electricity_bus['sequences'][(('bus_electricity_mg', 'transformer_pcc_feedin'), 'flow')]

        if setting_save_flows_electricity_mg == True:
            from config import output_folder
            electricity_mg_flows = pd.DataFrame(demand_supply.values, columns=['Demand supply'], index=demand_supply.index)
            if case_dict['pv_fixed_capacity'] != None:
                electricity_mg_flows = electricity_mg_flows.join(
                    pd.DataFrame(pv_gen.values, columns=['PV generation'], index=pv_gen.index))
            if case_dict['genset_fixed_capacity'] != None:
                electricity_mg_flows = electricity_mg_flows.join(
                pd.DataFrame(genset.values, columns=['GenSet'], index=genset.index))
            if case_dict['storage_fixed_capacity'] != None:
                electricity_mg_flows = electricity_mg_flows.join(
                pd.DataFrame(discharge.values, columns=['Discharge storage'], index=discharge.index))
                electricity_mg_flows = electricity_mg_flows.join(
                pd.DataFrame(charge.values, columns=['Charge storage'], index=charge.index))

            electricity_mg_flows = electricity_mg_flows.join(
                pd.DataFrame(excess.values, columns=['Excess electricity'], index=excess.index))

            if case_dict['allow_shortage'] == True:
                electricity_mg_flows = electricity_mg_flows.join(
                    pd.DataFrame(shortage.values, columns=['Supply shortage'], index=shortage.index))

            if case_dict['pcc_consumption_fixed_capacity'] != None:
                electricity_mg_flows = electricity_mg_flows.join(
                    pd.DataFrame(consumption.values, columns=['Consumption from main grid'], index=consumption.index))

            if case_dict['pcc_feedin_fixed_capacity'] != None:
                electricity_mg_flows = electricity_mg_flows.join(
                    pd.DataFrame(feedin.values, columns=['Feed into main grid'], index=feedin.index))

            electricity_mg_flows.to_csv(output_folder + '/electricity_mg/' + case_dict['case_name'] + filename + '_electricity_mg.csv')

        if plt is not None and display_graphs_flows_electricity_mg == True:
            logging.debug('Plotting: Electricity bus')
            # plot each flow to/from electricity bus with appropriate name
            if case_dict['pv_fixed_capacity'] != None:
                pv_gen.plot(kind='line', drawstyle='steps-post', label='PV generation')
            demand_supply.plot(kind='line', drawstyle='steps-post', label='Demand supply')
            if case_dict['genset_fixed_capacity'] != None:
                genset.plot(kind='line', drawstyle='steps-post', label='GenSet')
            if case_dict['storage_fixed_capacity'] != None:
                discharge.plot(kind='line', drawstyle='steps-post', label='Discharge storage')
                charge.plot(kind='line', drawstyle='steps-post', label='Charge storage')
            excess.plot(kind='line', drawstyle='steps-post', label='Excess electricity')

            if case_dict['allow_shortage'] == True:
                shortage.plot(kind='line', drawstyle='steps-post', label='Supply shortage')

            if case_dict['pcc_consumption_fixed_capacity'] != None:
                consumption.plot(kind='line', drawstyle='steps-post', label='Consumption from main grid')

            if case_dict['pcc_feedin_fixed_capacity'] != None:
                feedin.plot(kind='line', drawstyle='steps-post', label='Feed into main grid')

            plt.legend(loc='upper right')
            plt.show()
        return

    def draw(energysystem):
        '''
        Compare with https://oemof.readthedocs.io/en/stable/api/oemof.html?highlight=graph#module-oemof.graph for additional settings
        '''
        import oemof.graph as graph
        import networkx as nx
        import matplotlib.pyplot as plt
        from config import output_folder

        energysystem_graph = graph.create_nx_graph(energysystem, filename=output_folder+'/'+'case_graph')

        return
    ###### Show ######