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

    def project_annuity(oemof_results, experiment, capacities, case_name):
        from config import evaluated_days
        '''
        Necessary in oemof_results: 
        consumption_fuel, consumption_main_grid_annual, feedin_main_grid_annual, demand_annual_supplied_kWh
        '''
        annuity = oemof_results['objective_value']
        annuity = annuity * 365 / evaluated_days
        annuity_operational = annuity

        oemof_results = add_results.capacities(oemof_results, capacities)
        oemof_results = add_results.annuities(oemof_results, experiment, capacities, evaluated_days)
        oemof_results = add_results.costs(oemof_results, experiment)
        oemof_results = add_results.expenditures(oemof_results, experiment)

        operation_costs = annuity

        # Adding costs of fixed components where necessary for...
        # ...pv
        if case_name in ['offgrid_fix', 'interconnected_buysell']:
            annuity = annuity + oemof_results['annuity_pv']
        else:
            annuity_operational = annuity_operational -  oemof_results['annuity_pv']


        # ... storage
        if case_name in ['offgrid_fix', 'interconnected_buysell']:
            annuity = annuity + oemof_results['annuity_storage']
        else:
            annuity_operational = annuity_operational -  oemof_results['annuity_storage']

        # ...generators
        if case_name in ['base_oem_with_min_loading', 'offgrid_fix', 'interconnected_buysell']:
            annuity = annuity + oemof_results['annuity_genset']
        else:
            annuity_operational = annuity_operational -  oemof_results['annuity_genset']

        # ...point of coupling
        if case_name in ['interconnected_buysell']:
            annuity = annuity + oemof_results['annuity_pcoupling']
            # no else, as pcoupling is not optimized in ANY case

        # ...main grid extension
        if case_name in ['interconnected_buysell']:
            annuity = annuity + oemof_results['annuity_grid_extension']
            # no else, as extension costs are not variable

        # ... project costs
        annuity = annuity + experiment['annuities_project_fix']
        npv = annuity * experiment['annuity_factor']
        costs_operation = annuity_operational * experiment['annuity_factor']

        # Expenditures are not part of the (variable) operation costs:
        annuities_operational = annuity_operational \
                              - oemof_results['expenditures_fuel_annual'] \
                              - oemof_results['expenditures_main_grid_consumption_annual'] \
                              + oemof_results['revenue_main_grid_feedin_annual']

        # The costs saved as annuity_operation include the variable operation costs
        # - but yearly operation costs for components are included in their annuity!
        oemof_results.update({
            'annuity_operational':  annuity_operational,
            'costs_operation':      costs_operation,
            'annuity':              annuity,
            'npv':                  npv,
            'lcoe':                 annuity/oemof_results['demand_annual_supplied_kWh']})

        return oemof_results

    def capacities(oemof_results, capacities):
        oemof_results.update({'capacity_pv_kWp': capacities['capacity_pv_kWp']})
        oemof_results.update({'capacity_storage_kWh': capacities['capacity_storage_kWh']})
        oemof_results.update({'capacity_genset_kW': capacities['capacity_genset_kW']})
        oemof_results.update({'capacity_pcoupling_kW': capacities['capacity_pcoupling_kW']})
        return oemof_results

    def annuities(oemof_results, experiment, capacities, evaluated_days):
        oemof_results.update({
            'annuity_pv': experiment['pv_cost_annuity'] * capacities['capacity_pv_kWp'] * 365 / evaluated_days,
            'annuity_storage': experiment['storage_cost_annuity'] * capacities[
                'capacity_storage_kWh'] * 365 / evaluated_days,
            'annuity_genset': experiment['genset_cost_annuity'] * capacities[
                'capacity_genset_kW'] * 365 / evaluated_days,
            'annuity_pcoupling': experiment['pcoupling_cost_annuity'] * capacities[
                'capacity_pcoupling_kW'] * 365 / evaluated_days,
            'annuity_grid_extension': experiment['maingrid_extension_cost_annuity'] * experiment[
                'maingrid_distance'] * 365 / evaluated_days,
            'annuity_project_fix': experiment['project_cost_annuity'] * 365 / evaluated_days})

    def costs(oemof_results, experiment):
        oemof_results.update({
            'costs_pv': experiment['annuity_pv'] * experiment['annuity_factor'],
            'costs_storage': experiment['annuity_storage'] * experiment['annuity_factor'],
            'costs_genset': experiment['annuity_genset'] * experiment['annuity_factor'],
            'costs_pcoupling': experiment['annuity_pcoupling'] * experiment['annuity_factor'],
            'costs_grid_extension': experiment['annuity_grid_extension'] * experiment['annuity_factor'],
            'costs_project_fix': experiment['annuity_project_fix'] * experiment['annuity_factor']})
        return oemof_results

    def expenditures(oemof_results, experiment):
        '''
        Necessary in oemof_results: consumption_fuel, consumption_main_grid_annual, feedin_main_grid_annual
        '''
        # annual
        oemof_results.update({
            'expenditures_fuel_annual':
                oemof_results['consumption_fuel'] * experiment['price_fuel'] / experiment['combustion_value_fuel'],
            'expenditures_main_grid_consumption_annual':
                oemof_results['consumption_main_grid_annual'] * experiment['maingrid_electricity_price'],
            'revenue_main_grid_feedin_annual':
                oemof_results['feedin_main_grid_annual'] * experiment['maingrid_feedin_tariff']})

        # overall present value
        oemof_results.update({
            'expenditures_fuel_total':
                oemof_results['expenditures_fuel_annual'] * experiment['annuity_factor'],
            'expenditures_main_grid_consumption_total':
                oemof_results['expenditures_main_grid_consumption_annual'] * experiment['annuity_factor'],
            'revenues_main_grid_feedin_total':
                oemof_results['revenue_main_grid_feedin_annual'] * experiment['annuity_factor']})
        return oemof_results

class oemofmodel():

    ######## Processing ########
    def process_basic(micro_grid_system, experiment, demand_profile, case_name):
        # define an alias for shorter calls below (optional)
        results = micro_grid_system.results['main']
        meta = micro_grid_system.results['meta']

        # get all variables of a specific component/bus
        generic_storage = outputlib.views.node(results, 'generic_storage')
        electricity_bus = outputlib.views.node(results, 'bus_electricity_mg')
        fuel_bus = outputlib.views.node(results, 'bus_fuel')
        oemofmodel.plot_bus_electricity_mg(electricity_bus, case_name)
        oemofmodel.plot_storage(generic_storage)
        oemofmodel.print_oemof_meta_main_invest(meta, electricity_bus, case_name)

        total_supplied_demand   = electricity_bus['sequences'][(('bus_electricity_mg', 'sink_demand'), 'flow')].sum()
        total_diesel_generation = electricity_bus['sequences'][(('transformer_fuel_generator', 'bus_electricity_mg'), 'flow')].sum()
        res_share = abs(1 - total_diesel_generation / total_supplied_demand)

        total_fuel_consumption = fuel_bus['sequences'][(('source_fuel', 'bus_fuel'), 'flow')].sum()
        total_supplied_demand = electricity_bus['sequences'][(('bus_electricity_mg', 'sink_demand'), 'flow')].sum()

        from config import evaluated_days
        total_fuel_consumption = total_fuel_consumption * 365 / evaluated_days
        total_supplied_demand = total_supplied_demand * 365 / evaluated_days
        total_demand = sum(demand_profile)
        # todo: if freq=15 min, this has to be adjusted!

        # Defining oemof_results (first entries).
        # Added in main_tool: 'grid_reliability', 'grid_total_blackout_duration', 'grid_number_of_blackouts' (only for cases)
        # Specific values added in process_fix/process_oem
        oemof_results = {
            'case':                         case_name,
            'filename':                     'results_' + case_name + experiment['filename'],
            'res_share':                    res_share,
            'consumption_fuel':             total_fuel_consumption,
            'demand_annual_supplied_kWh':   total_supplied_demand,
            'demand_annual_kWh':            total_demand,
            'demand_peak_kW':               max(demand_profile),
            'objective_value':              meta['objective']
             }

        return results, meta, electricity_bus, oemof_results

    def process_fix(micro_grid_system, case_name, capacity_batch, experiment, demand_profile):
        results, meta, electricity_bus, oemof_results = oemofmodel.process_basic(micro_grid_system, experiment, demand_profile, case_name)


        #oemof_results = project_annuity(oemof_results, experiment, capacities, case_name)

        annuity = experiment['pv_cost_annuity']*capacity_batch['pv_capacity_kWp'] +\
                experiment['genset_cost_annuity']*capacity_batch['genset_capacity_kW'] +\
                experiment['storage_cost_annuity'] * capacity_batch['storage_capacity_kWh'] + \
                experiment['pcoupling_cost_annuity'] * capacity_batch['pcoupling_capacity_kW'] + \
                experiment['project_cost_annuity'] +\
                meta['objective'] # here, objective function only gives the additional VARIABLE costs!

        from config import evaluated_days
        annuity = annuity * 365 / evaluated_days

        npv = annuity * experiment['annuity_factor']

        oemof_results.update({'npv':  npv})
        oemof_results.update({'annuity': annuity})
        oemof_results.update({'lcoe': annuity/oemof_results['demand_annual_supplied_kWh']})

        oemof_results.update({'capacity_pv_kWp': capacity_batch['pv_capacity_kWp']})
        oemof_results.update({'capacity_storage_kWh': capacity_batch['storage_capacity_kWh']})
        oemof_results.update({'capacity_genset_kW': capacity_batch['genset_capacity_kW']})

        oemof_results.update({'pv_investment':
                                  experiment['pv_cost_annuity']*capacity_batch['pv_capacity_kWp']*experiment['annuity_factor']})
        oemof_results.update({'storage_investment':
                                  experiment['genset_cost_annuity']*capacity_batch['genset_capacity_kW']*experiment['annuity_factor']})
        oemof_results.update({'genset_investment':
                                  experiment['storage_cost_annuity'] * capacity_batch['storage_capacity_kWh']*experiment['annuity_factor']})




        logging.info('    Dispatch optimization for case "' + case_name + '" finished, with renewable share of ' +
                     str(round(oemof_results['res_share']*100,2)) + ' percent.')

        return oemof_results

    def process_oem(micro_grid_system, case_name, pv_generation_max, experiment, demand_profile):

        results, meta, electricity_bus, oemof_results = oemofmodel.process_basic(micro_grid_system, experiment, demand_profile, case_name)

        annuity = meta['objective'] + experiment['project_cost_annuity']
        if case_name == "base_oem_with_min_loading":
            annuity = annuity + experiment['genset_cost_annuity']* max(demand_profile)

        # todo: if case oem of grid-tied mg, add maingrid_extension_cost_annuity

        from config import evaluated_days
        annuity               = annuity * 365 / evaluated_days  # scaling to full year

        oemof_results.update({'annuity':    annuity})
        oemof_results.update({'lcoe':       annuity/oemof_results['demand_annual_supplied_kWh']})
        oemof_results.update({'npv':        annuity*experiment['annuity_factor']})

        # ToDo issue for OEMOF: How to evaluate battery capacity
        capacity_battery = 1/experiment['storage_Crate']*(electricity_bus['scalars'][(('generic_storage', 'bus_electricity_mg'), 'invest')]
                              + electricity_bus['scalars'][(('bus_electricity_mg', 'generic_storage'), 'invest')])/2
        oemof_results.update({'capacity_storage_kWh': capacity_battery})

        if pv_generation_max > 1:
            oemof_results.update({'capacity_pv_kWp': electricity_bus['scalars'][(('source_pv', 'bus_electricity_mg'), 'invest')]* pv_generation_max })
        elif pv_generation_max > 0 and pv_generation_max < 1:
            oemof_results.update({'capacity_pv_kWp': electricity_bus['scalars'][(('source_pv', 'bus_electricity_mg'), 'invest')] / pv_generation_max })
        else:
            logging.warning("Error, Strange PV behaviour (PV gen < 0)")

        if case_name == "base_oem":
            # Optimized generator capacity
            oemof_results.update({'capacity_genset_kW': electricity_bus['scalars'][(('transformer_fuel_generator', 'bus_electricity_mg'), 'invest')]})
        elif case_name == "base_oem_with_min_loading":
            # Genset capacity equals peak demand
            oemof_results.update({'capacity_genset_kW': max(demand_profile)})
        # todo: as soon as pcc optimized, put here

        logging.info ('    Exact OEM results of case "' + case_name + '" : \n'
                      +'    '+'  '+ '    ' + '    ' + '    ' + str(round(oemof_results['capacity_storage_kWh'],3)) + ' kWh battery, '
                      + str(round(oemof_results['capacity_pv_kWp'],3)) + ' kWp PV, '
                      + str(round(oemof_results['capacity_genset_kW'],3)) + ' kW genset '
                      + 'at a renewable share of ' + str(round(oemof_results['res_share']*100,2)) + ' percent.')

        capacities_base = {
            'capacity_pv_kWp': oemof_results['capacity_pv_kWp'],
            'capacity_storage_kWh': oemof_results['capacity_storage_kWh'],
            'capacity_genset_kW': oemof_results['capacity_genset_kW'],
            'capacity_pcoupling_kW': 0
                            }
        # todo as soon as pcc optimized or more cases optimized than base_oem / base_oem_with_min_loading, redefine capacity here
        if case_name == "base_oem" or case_name == "base_oem_with_min_loading":
            capacities_base.update({"pcoupling_capacity_kW": 0})

        oemof_results.update({'pv_investment':
                                  experiment['pv_cost_annuity']*capacities_base['capacity_pv_kWp']*experiment['annuity_factor']})
        oemof_results.update({'storage_investment':
                                  experiment['genset_cost_annuity']*capacities_base['capacity_storage_kWh']*experiment['annuity_factor']})
        oemof_results.update({'genset_investment':
                                  experiment['storage_cost_annuity'] * capacities_base['capacity_genset_kW']*experiment['annuity_factor']})

        return oemof_results, capacities_base

    def process_oem_batch(capacities_base, case_name):
        from input_values import round_to_batch
        capacities_base.update({'pv_capacity_kWp': round (0.5+capacities_base['capacity_pv_kWp']/round_to_batch['PV'])
                                                  *round_to_batch['PV']}) # immer eher 0.25 capacity mehr als eigentlich nötig
        capacities_base.update({'genset_capacity_kW': round(0.5+capacities_base['capacity_genset_kW'] / round_to_batch['GenSet']) *
                                                  round_to_batch['GenSet']})
        capacities_base.update({'storage_capacity_kWh': round(0.5+capacities_base['capacity_pcoupling_kW'] / round_to_batch['Storage']) *
                                                  round_to_batch['Storage']})
        capacities_base.update(
            {'pcoupling_capacity_kW': round(0.5 + capacities_base['pcoupling_capacity_kW'] / round_to_batch['Pcoupling']) *
                                     round_to_batch['Pcoupling']})
        logging.debug ('    Equivalent batch capacities of base OEM for dispatch OEM in case "' + case_name + '": \n'
                      + '    ' + '  ' + '    ' + '    ' + '    ' + str(capacities_base['storage_capacity_kWh']) + ' kWh battery, '
                      + str(capacities_base['pv_capacity_kWp']) + ' kWp PV, '
                      + str(capacities_base['genset_capacity_kW']) + ' kW genset.')
        return capacities_base

    ######## Textblocks ########
    def textblock_fix():
        logging.debug('    FIXED CAPACITIES (Dispatch optimization)')
        logging.debug('Create oemof objects for Micro Grid System (off-grid)')

    def textblock_oem():
        logging.debug('    VARIABLE CAPACITIES (OEM)')
        logging.debug('Create oemof objects for Micro Grid System (off-grid)')
    ######## Textblocks ########

    ######## Simulation control ########
    def initialize_model():
        from config import date_time_index
        logging.debug('Initialize energy system dataframe')
        # create energy system
        micro_grid_system = solph.EnergySystem(timeindex=date_time_index)
        return micro_grid_system

    def simulate(micro_grid_system, file_name):
        from config import solver, solver_verbose, output_folder, setting_save_lp_file, cmdline_option, cmdline_option_value
        logging.debug('Initialize the energy system to be optimized')
        model = solph.Model(micro_grid_system)
        logging.debug('Solve the optimization problem')
        model.solve(solver          =   solver,
                    solve_kwargs    =   {'tee': solver_verbose}, # if tee_switch is true solver messages will be displayed
                    cmdline_options =   {cmdline_option:    str(cmdline_option_value)})   #ratioGap allowedGap mipgap

        if setting_save_lp_file == True:
            model.write(output_folder + '/model_' + file_name + '.lp',
                        io_options={'symbolic_solver_labels': True})

        # add results to the energy system to make it possible to store them.
        micro_grid_system.results['main'] = outputlib.processing.results(model)
        micro_grid_system.results['meta'] = outputlib.processing.meta_results(model)
        return micro_grid_system

    def load_energysystem_lp():
        # based on lp file
        return

    def store_results(micro_grid_system, file_name):
        # store energy system with results
        from config import output_folder, setting_save_oemofresults
        if setting_save_oemofresults == True:
            micro_grid_system.dump(dpath=output_folder, filename = file_name + ".oemof" )
            logging.debug('Stored results in ' + output_folder + '/' + file_name + ".oemof")
        return micro_grid_system

    def filename(case_name, experiment_name):
        from config import output_file
        file_name = output_file + "_" + case_name + experiment_name
        return file_name

    def load_oemof_results(file_name):
        from config import output_folder
        logging.debug('Restore the energy system and the results.')
        micro_grid_system = solph.EnergySystem()
        micro_grid_system.restore(dpath=output_folder,
                                  filename=file_name + ".oemof")
        return micro_grid_system

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
    def plot_storage(custom_storage):
        from config import display_graphs_simulation
        if plt is not None and display_graphs_simulation == True:
            logging.debug('Plotting: Generic storage')
            custom_storage['sequences'][(('generic_storage', 'None'), 'capacity')].plot(kind='line',
                                                                                        drawstyle='steps-post',
                                                                                        label='Stored capacity in kWh')
            custom_storage['sequences'][(('generic_storage', 'bus_electricity_mg'), 'flow')].plot(kind='line',
                                                                                                  drawstyle='steps-post',
                                                                                                  label='Discharge storage')
            custom_storage['sequences'][(('bus_electricity_mg', 'generic_storage'), 'flow')].plot(kind='line',
                                                                                                  drawstyle='steps-post',
                                                                                                  label='Charge storage')
            plt.legend(loc='upper right')
            plt.show()
        return

    def plot_bus_electricity_mg(electricity_bus, case_name):
        from config import allow_shortage, display_graphs_simulation
        if plt is not None and display_graphs_simulation == True:
            logging.debug('Plotting: Electricity bus')
            # plot each flow to/from electricity bus with appropriate name
            electricity_bus['sequences'][(('source_pv', 'bus_electricity_mg'), 'flow')].plot(
                kind='line', drawstyle='steps-post', label='PV generation')
            electricity_bus['sequences'][(('bus_electricity_mg', 'sink_demand'), 'flow')].plot(
                kind='line', drawstyle='steps-post', label='Demand supply')
            electricity_bus['sequences'][(('transformer_fuel_generator', 'bus_electricity_mg'), 'flow')].plot(
                kind='line', drawstyle='steps-post', label='GenSet')
            electricity_bus['sequences'][(('generic_storage', 'bus_electricity_mg'), 'flow')].plot(
                kind='line', drawstyle='steps-post', label='Discharge storage')
            electricity_bus['sequences'][(('bus_electricity_mg', 'generic_storage'), 'flow')].plot(
                kind='line', drawstyle='steps-post', label='Charge storage')
            electricity_bus['sequences'][(('bus_electricity_mg', 'sink_excess'), 'flow')].plot(
                kind='line', drawstyle='steps-post', label='Excess electricity')

            if allow_shortage == True:
                electricity_bus['sequences'][(('source_shortage', 'bus_electricity_mg'), 'flow')].plot(
                    kind='line', drawstyle='steps-post', label='Supply shortage')

            if case_name == "interconnected_buysell" or case_name =="interconnected_buy":
                electricity_bus['sequences'][(('transformer_pcc_consumption', 'bus_electricity_mg'), 'flow')].plot(
                    kind='line', drawstyle='steps-post', label='Consumption from main grid')

            if case_name == "interconnected_buysell":
                electricity_bus['sequences'][(('bus_electricity_mg', 'transformer_pcc_feedin'), 'flow')].plot(
                    kind='line', drawstyle='steps-post', label='Feed into main grid')

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