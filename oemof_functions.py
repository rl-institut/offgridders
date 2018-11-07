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

class generatemodel():
    ######## Busses ########
    def bus_basic(micro_grid_system):
        bus_fuel = solph.Bus(label="bus_fuel")
        bus_electricity_mg = solph.Bus(label="bus_electricity_mg")
        micro_grid_system.add(bus_electricity_mg, bus_fuel)
        return micro_grid_system, bus_fuel, bus_electricity_mg

    def bus_el_ng(micro_grid_system):
        bus_electricity_ng = solph.Bus(label="bus_electricity_ng")
        micro_grid_system.add(bus_electricity_ng)
        return micro_grid_system, bus_electricity_ng
    ######## Busses ########

    ######## Sources ########
    def fuel(micro_grid_system, bus_fuel):
        from input_values import fuel_price
        source_fuel = solph.Source(label="source_fuel",
                                   outputs={bus_fuel: solph.Flow(
                                       variable_costs=fuel_price / 9.41)})
        micro_grid_system.add(source_fuel)
        return micro_grid_system, bus_fuel

    def shortage(micro_grid_system, bus_electricity_mg, demand_profile):
        from config import var_costs_unsupplied_load, max_share_unsupplied_load
        source_shortage = solph.Source(label="source_shortage",
                                       outputs={bus_electricity_mg: solph.Flow(
                                           variable_costs=var_costs_unsupplied_load,
                                           nominal_value=max_share_unsupplied_load * sum(demand_profile),
                                           summed_max=1)})
        micro_grid_system.add(source_shortage)
        return micro_grid_system, bus_electricity_mg
    ######## Sources ########

    ######## Components ########
    def pv_fix(micro_grid_system, bus_electricity_mg, pv_generation_per_kWp):
        from input_values import cap_pv
        source_pv = solph.Source(label="source_pv",
                                 outputs={bus_electricity_mg: solph.Flow(label='PV generation',
                                                                         actual_value=pv_generation_per_kWp,
                                                                         fixed=True,
                                                                         nominal_value=cap_pv
                                                                         )})

        micro_grid_system.add(source_pv)
        return micro_grid_system, bus_electricity_mg

    def pv_oem(micro_grid_system, bus_electricity_mg, pv_generation_per_kWp):
        from input_values import cost_data
        pv_norm = pv_generation_per_kWp / max(pv_generation_per_kWp)
        if pv_norm.any() > 1: logging.warning("Error, PV generation not normalized, greater than 1")
        if pv_norm.any() < 0: logging.warning("Error, PV generation negative")

        source_pv = solph.Source(label="source_pv",
                                 outputs={bus_electricity_mg: solph.Flow(label='PV generation',
                                                                         actual_value=pv_norm,
                                                                         fixed=True,
                                                                         investment=solph.Investment(
                                                                             ep_costs=cost_data.loc['annuity', 'PV'])
                                                                         )})
        micro_grid_system.add(source_pv)
        return micro_grid_system, bus_electricity_mg

    def transformer_fix(micro_grid_system, bus_fuel, bus_electricity_mg):
        from input_values import cap_fuel_gen
        transformer_fuel_generator = solph.Transformer(label="transformer_fuel_generator",
                                                       inputs={bus_fuel: solph.Flow()},
                                                       outputs={bus_electricity_mg: solph.Flow(
                                                           nominal_value=cap_fuel_gen)},
                                                       conversion_factors={
                                                           bus_electricity_mg: 0.58})  # is efficiency of the generator?? Then this should later on be included as a function of the load factor

        micro_grid_system.add(transformer_fuel_generator)
        return micro_grid_system, bus_fuel, bus_electricity_mg

    def transformer_oem(micro_grid_system, bus_fuel, bus_electricity_mg):
        from input_values import cost_data
        transformer_fuel_generator = solph.Transformer(label="transformer_fuel_generator",
                                                       inputs={bus_fuel: solph.Flow()},
                                                       outputs={bus_electricity_mg: solph.Flow(
                                                           investment=solph.Investment(
                                                               ep_costs=cost_data.loc['annuity', 'GenSet']))},
                                                       conversion_factors={bus_electricity_mg: 0.58})
        micro_grid_system.add(transformer_fuel_generator)
        return micro_grid_system, bus_fuel, bus_electricity_mg

    def storage_fix(micro_grid_system, bus_electricity_mg):
        from input_values import cap_storage
        generic_storage = solph.components.GenericStorage(
            label='generic_storage',
            nominal_capacity=cap_storage,
            inputs={bus_electricity_mg: solph.Flow(
                nominal_value=cap_storage / 6)},  # probably the maximum charge/discharge possible in one timestep
            outputs={bus_electricity_mg: solph.Flow(
                nominal_value=cap_storage / 6,
                variable_costs=0.0)},
            capacity_loss=0.00,  # from timestep to timestep? what is this?
            initial_capacity=0,  # in terms of SOC?
            inflow_conversion_factor=1,  # storing efficiency?
            outflow_conversion_factor=0.8)  # efficiency of feed-in-stored?

        micro_grid_system.add(generic_storage)
        return micro_grid_system, bus_electricity_mg

    def storage_oem(micro_grid_system, bus_electricity_mg):
        from input_values import cost_data
        generic_storage = solph.components.GenericStorage(
            label='generic_storage',
            inputs={bus_electricity_mg: solph.Flow()},
            # 10077997/6 is probably the maximum charge/discharge possible in one timestep
            outputs={bus_electricity_mg: solph.Flow(variable_costs=0.0)},
            capacity_loss=0.00,  # from timestep to timestep? what is this?
            inflow_conversion_factor=1,  # storing efficiency?
            outflow_conversion_factor=0.8,  # efficiency of feed-in-stored?
            investment=solph.Investment(ep_costs=cost_data.loc['annuity', 'Storage']),
            invest_relation_input_capacity=1 / 6,
            invest_relation_output_capacity=1 / 6
        )
        micro_grid_system.add(generic_storage)
        return micro_grid_system, bus_electricity_mg
    ######## Components ########

    ######## Sinks ########
    def excess(micro_grid_system, bus_electricity_mg):
        # create and add excess electricity sink to micro_grid_system - variable
        sink_excess = solph.Sink(label="sink_excess",
                                 inputs={bus_electricity_mg: solph.Flow()})
        micro_grid_system.add(sink_excess)
        return micro_grid_system, bus_electricity_mg

    def demand(micro_grid_system, bus_electricity_mg, demand_profile):
        # create and add demand sink to micro_grid_system - fixed
        sink_demand = solph.Sink(label="sink_demand",
                                 inputs={bus_electricity_mg: solph.Flow(
                                     actual_value=demand_profile,
                                     nominal_value=1,
                                     fixed=True)})
        micro_grid_system.add(sink_demand)
        return micro_grid_system, bus_electricity_mg
    ######## Sinks ########

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

    def simulate(micro_grid_system):
        from config import solver, solver_verbose, output_folder, output_file, setting_lp_file
        logging.debug('Initialize the energy system to be optimized')
        model = solph.Model(micro_grid_system)
        logging.debug('Solve the optimization problem')
        model.solve(solver=solver,
                    solve_kwargs={'tee': solver_verbose})  # if tee_switch is true solver messages will be displayed
        if setting_lp_file == True: model.write('./my_model.lp', io_options={'symbolic_solver_labels': True})

        # add results to the energy system to make it possible to store them.
        micro_grid_system.results['main'] = outputlib.processing.results(model)
        micro_grid_system.results['meta'] = outputlib.processing.meta_results(model)
        return micro_grid_system
    ######## Simulation control ########

    ######## Processing ########
    def load_energysystem():
        return

    def store_results(micro_grid_system, case_name):
        # todo Enter check for directory and create directory here!
        # store energy system with results
        from config import output_folder, output_file
        micro_grid_system.dump(dpath=output_folder, filename=output_file+ '_' + case_name + ".oemof")
        logging.debug('Stored results in ' + output_folder + '/' + output_file + '_' + case_name + '.oemof')
        return micro_grid_system

    def load_results():
        from config import output_folder, output_file
        logging.debug('Restore the energy system and the results.')
        micro_grid_system = solph.EnergySystem()
        micro_grid_system.restore(dpath=output_folder, filename=output_file+".oemof")
        return micro_grid_system

    def process(micro_grid_system, case_name, get_el_bus):
        # define an alias for shorter calls below (optional)
        results = micro_grid_system.results['main']
        meta = micro_grid_system.results['meta']
        storage = micro_grid_system.groups['generic_storage']

        # get all variables of a specific component/bus
        generic_storage = outputlib.views.node(results, 'generic_storage')
        electricity_bus = outputlib.views.node(results, 'bus_electricity_mg')
        generatemodel.plot_el_mg(electricity_bus)
        generatemodel.plot_storage(generic_storage)

        # print the solver results
        logging.debug('********* Meta results *********')
        logging.debug(meta)
        # print the sums of the flows around the electricity bus
        logging.debug('********* Main results *********')
        logging.debug(electricity_bus['sequences'].sum(axis=0))

        if get_el_bus == True:
            return electricity_bus
        else:
            return logging.info('    Dispatch optimization for case "' + case_name + '" finished, with renewable share of ' +
            str(round((1 - electricity_bus['sequences'][(('transformer_fuel_generator', 'bus_electricity_mg'), 'flow')].sum()
             / electricity_bus['sequences'][(('bus_electricity_mg', 'sink_demand'), 'flow')].sum()) * 100)) +
                                ' percent.')

    def process_oem(electricity_bus, case_name):
        oem_results = pd.DataFrame({'storage_invest_kWh': [electricity_bus['scalars'][(('generic_storage', 'bus_electricity_mg'), 'invest')]],
                                           'pv_invest_kW': [electricity_bus['scalars'][(('source_pv', 'bus_electricity_mg'), 'invest')]],
                                           'genset_invest_kW': [electricity_bus['scalars'][(('transformer_fuel_generator', 'bus_electricity_mg'), 'invest')]],
                                           'res_share_perc': [(1 - electricity_bus['sequences'][(('transformer_fuel_generator', 'bus_electricity_mg'), 'flow')].sum()
                                                          / electricity_bus['sequences'][(('bus_electricity_mg', 'sink_demand'), 'flow')].sum())*100]},
                                          index=[case_name])

        logging.info ('    OEM results of case "' + case_name + '" : ' + str(round(oem_results['storage_invest_kWh'][case_name])) + ' kWh battery, ' +
                                           str(round(oem_results['pv_invest_kW'][case_name])) + ' kWp PV, ' +
                                                     str(round(oem_results['genset_invest_kW'][case_name])) + ' kW genset at a renewable share of ' +
                                                               str(round(oem_results['res_share_perc'][case_name])) + ' percent.')
        return oem_results

    ######## Processing ########

    ####### Show #######
    def plot_storage(custom_storage):
        from config import display_graphs_simulation
        if plt is not None and display_graphs_simulation == True:
            logging.debug('Plotting: Generic storage')
            custom_storage['sequences'][(('generic_storage', 'None'), 'capacity')].plot(kind='line',
                                                                                        drawstyle='steps-post',
                                                                                        label='??((generic_storage, None), capacity)??')
            custom_storage['sequences'][(('generic_storage', 'bus_electricity_mg'), 'flow')].plot(kind='line',
                                                                                                  drawstyle='steps-post',
                                                                                                  label='Discharge storage')
            custom_storage['sequences'][(('bus_electricity_mg', 'generic_storage'), 'flow')].plot(kind='line',
                                                                                                  drawstyle='steps-post',
                                                                                                  label='Charge storage')
            plt.legend(loc='upper right')
            plt.show()
        return

    def plot_el_mg(electricity_bus):
        from config import allow_shortage, display_graphs_simulation
        if plt is not None and display_graphs_simulation == True:
            logging.debug('Plotting: Electricity bus')
            # plot each flow to/from electricity bus with appropriate name
            electricity_bus['sequences'][(('source_pv', 'bus_electricity_mg'), 'flow')].plot(kind='line',
                                                                                             drawstyle='steps-post',
                                                                                             label='PV generation')
            electricity_bus['sequences'][(('bus_electricity_mg', 'sink_demand'), 'flow')].plot(kind='line',
                                                                                               drawstyle='steps-post',
                                                                                               label='Demand supply')
            electricity_bus['sequences'][(('transformer_fuel_generator', 'bus_electricity_mg'), 'flow')].plot(
                kind='line', drawstyle='steps-post', label='GenSet')
            electricity_bus['sequences'][(('generic_storage', 'bus_electricity_mg'), 'flow')].plot(kind='line',
                                                                                                   drawstyle='steps-post',
                                                                                                   label='Discharge storage')
            electricity_bus['sequences'][(('bus_electricity_mg', 'generic_storage'), 'flow')].plot(kind='line',
                                                                                                   drawstyle='steps-post',
                                                                                                   label='Charge storage')
            electricity_bus['sequences'][(('bus_electricity_mg', 'sink_excess'), 'flow')].plot(kind='line',
                                                                                               drawstyle='steps-post',
                                                                                               label='Excess electricity')
            if allow_shortage == True: electricity_bus['sequences'][
                (('source_shortage', 'bus_electricity_mg'), 'flow')].plot(kind='line', drawstyle='steps-post',
                                                                          label='Supply shortage')
            plt.legend(loc='upper right')
            plt.show()
        return
    ###### Show ######