"""
Following excample:
https://github.com/oemof/oemof_examples/blob/master/examples/oemof_0.2/basic_example/basic_example.py#L84

Energy system modeled: Micro Grid with fixed capacities

            input/output    bus_fuel        bus_electricity     flow
                    |               |               |
                    |               |               |
source: pv          |------------------------------>|       generate_pv (fix)
                    |               |               |
source: fossil_fuel |-------------->|               |       fossil_fuel_in (var)
                    |               |               |
trafo: generator    |<--------------|               |       fossil_fuel_use (var)
                    |------------------------------>|       generate_fuel (var)
                    |               |               |
storage: battery    |<------------------------------|       battery_charge (var)
                    |------------------------------>|       battery_discharge (var)
                    |               |               |
sink: demand        |<------------------------------|       supply_demand (fix)
                    |               |               |
sink: excess        |<------------------------------|       supply_excess (var)
                    |               |               |

_____
Data used: None

_________
Requires:
oemof, matplotlib, demandlib, pvlib
tables, tkinter

"""

###############################################################################
# Imports and initialize
###############################################################################


# from oemof.tools import helpers
import pprint as pp
import oemof.solph as solph
import oemof.outputlib as outputlib

from oemof.tools import logger

import logging
# Logging
logger.define_logging(logfile='energy_system_main.log',
                      screen_level=logging.INFO,
                      file_level=logging.DEBUG)


# Try to import matplotlib librar
try:
    import matplotlib.pyplot as plt
except ImportError:
    logging.info('Attention! matplotlib could not be imported.')
    plt = None

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
        if pv_norm.any() > 1: logging.info("Error, PV generation not normalized, greater than 1")
        if pv_norm.any() < 0: logging.info("Error, PV generation negative")

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
        logging.info('    FIXED CAPACITIES (Dispatch optimization)')
        logging.info('Create oemof objects for Micro Grid System (off-grid)')

    def textblock_oem():
        logging.info('    VARIABLE CAPACITIES (OEM)')
        logging.info('Create oemof objects for Micro Grid System (off-grid)')
    ######## Textblocks ########

    ######## Simulation control ########
    def initialize_model():
        from config import date_time_index
        logging.info('Initialize the energy system')
        # create energy system
        micro_grid_system = solph.EnergySystem(timeindex=date_time_index)
        return micro_grid_system

    def simulate(micro_grid_system):
        from config import solver, solver_verbose, output_folder, output_file, setting_lp_file
        logging.info('Initialize the energy system to be optimized')
        model = solph.Model(micro_grid_system)
        logging.info('Solve the optimization problem')
        model.solve(solver=solver,
                    solve_kwargs={'tee': solver_verbose})  # if tee_switch is true solver messages will be displayed
        if setting_lp_file == True: model.write('./my_model.lp', io_options={'symbolic_solver_labels': True})
        logging.info('Store the energy system with the results.')

        # add results to the energy system to make it possible to store them.
        micro_grid_system.results['main'] = outputlib.processing.results(model)
        micro_grid_system.results['meta'] = outputlib.processing.meta_results(model)

        # todo Enter check for directory and create directory here!
        # store energy system with results
        micro_grid_system.dump(dpath=output_folder, filename=output_file)
        logging.info('Stored results in ' + output_folder + '/' + output_file)
        return
    ######## Simulation control ########

    ######## Processing ########
    def load_energysystem():
        return

    def load_results():
        from config import output_folder, output_file
        logging.info('Restore the energy system and the results.')
        micro_grid_system = solph.EnergySystem()
        micro_grid_system.restore(dpath=output_folder, filename=output_file)
        micro_grid_system.keys()
        return micro_grid_system

    def process_dispatch(micro_grid_system):
        # define an alias for shorter calls below (optional)
        results = micro_grid_system.results['main']
        storage = micro_grid_system.groups['generic_storage']

        # get all variables of a specific component/bus
        custom_storage = outputlib.views.node(results, 'generic_storage')
        electricity_bus = outputlib.views.node(results, 'bus_electricity_mg')
        generatemodel.plot_el_mg(custom_storage)
        generatemodel.plot_storage(electricity_bus)

        # print the solver results
        print('********* Meta results *********')
        pp.pprint(micro_grid_system.results['meta'])
        print('')
        # print the sums of the flows around the electricity bus
        print('********* Main results *********')
        print(electricity_bus['sequences'].sum(axis=0))
        return

    def process_oem(micro_grid_system):
        results = micro_grid_system.results['main']
        electricity_bus = outputlib.views.node(results, 'bus_electricity_mg')
        oem_results = electricity_bus['scalars']
        # installed capacity of storage in GWh
        # oem_results['storage_invest_kWh'] = (results[(generic_storage, None)]
        #                                    ['scalars']['invest'])

        # installed capacity of pv power plant in MW
        # oem_results['pv_invest_kW'] = (results[(source_pv, bus_electricity_mg)]
        #                              ['scalars']['invest'])

        # oem_results['res_share'] = (1 - results[(transformer_fuel_generator, bus_electricity_mg)]
        #                            ['sequences'].sum()/results[(bus_electricity_mg, sink_demand)]['sequences'].sum())

        return print(oem_results)
    ######## Processing ########

    ####### Show #######
    def plot_storage(custom_storage):
        if plt is not None:
            logging.info('Plotting: Generic storage')
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
        if plt is not None:
            logging.info('Plotting: Electricity bus')
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

###############################################################################
# Create Energy System with oemof
###############################################################################

class cases():
    from config import allow_shortage

    def mg_fixed(demand_profile, pv_generation):
        from config import allow_shortage
        micro_grid_system = generatemodel.initialize_model()
        generatemodel.textblock_fix()
        micro_grid_system, bus_fuel, bus_electricity_mg = generatemodel.bus_basic(micro_grid_system)
        micro_grid_system, bus_fuel = generatemodel.fuel(micro_grid_system, bus_fuel)
        if allow_shortage == True: micro_grid_system = generatemodel.shortage(micro_grid_system, bus_electricity_mg)
        micro_grid_system, bus_electricity_mg = generatemodel.demand(micro_grid_system, bus_electricity_mg, demand_profile)
        micro_grid_system, bus_electricity_mg = generatemodel.excess(micro_grid_system, bus_electricity_mg)
        micro_grid_system, bus_electricity_mg = generatemodel.pv_fix(micro_grid_system, bus_electricity_mg, pv_generation)
        micro_grid_system, bus_fuel, bus_electricity_mg = generatemodel.transformer_fix(micro_grid_system, bus_fuel, bus_electricity_mg)
        micro_grid_system, bus_electricity_mg = generatemodel.storage_fix(micro_grid_system, bus_electricity_mg)
        generatemodel.simulate(micro_grid_system)
        micro_grid_system = generatemodel.load_results()
        generatemodel.process_dispatch(micro_grid_system)

    def mg_oem(demand_profile, pv_generation):
        from config import allow_shortage
        micro_grid_system = generatemodel.initialize_model()
        generatemodel.textblock_oem()
        micro_grid_system, bus_fuel, bus_electricity_mg = generatemodel.bus_basic(micro_grid_system)
        micro_grid_system, bus_fuel = generatemodel.fuel(micro_grid_system, bus_fuel)
        if allow_shortage == True: micro_grid_system, bus_electricity_mg = generatemodel.shortage(micro_grid_system, bus_electricity_mg)
        micro_grid_system, bus_electricity_mg = generatemodel.demand(micro_grid_system, demand_profile, demand_profile)
        micro_grid_system, bus_electricity_mg = generatemodel.excess(micro_grid_system, bus_electricity_mg)
        micro_grid_system, bus_electricity_mg = generatemodel.pv_oem(micro_grid_system, bus_electricity_mg, pv_generation)
        micro_grid_system, bus_fuel, bus_electricity_mg = generatemodel.transformer_oem(micro_grid_system, bus_fuel, bus_electricity_mg)
        micro_grid_system, bus_electricity_mg = generatemodel.storage_oem(micro_grid_system, bus_electricity_mg)
        generatemodel.simulate(micro_grid_system)
        micro_grid_system = generatemodel.load_results()
        generatemodel.process_dispatch(micro_grid_system)
        generatemodel.process_oem(micro_grid_system)

from demand_profile import demand_profile

from input_values import demand_input
demand_profile = demand_profile.estimate(demand_input) # wh? kWh?
#------------- PV system------------------------------#
from pvlib_scripts import pvlib_scripts
from input_values import pv_system_location, location_name, pv_system_parameters, pv_composite_name
# Solar irradiance # todo check for units
solpos, dni_extra, airmass, pressure, am_abs, tl, cs = pvlib_scripts.irradiation(pv_system_location, location_name)
# PV generation # todo check for units
pv_generation_per_kWp, pv_module_kWp = pvlib_scripts.generation(pv_system_parameters, pv_composite_name, location_name, solpos, dni_extra, airmass, pressure, am_abs, tl, cs)

print (pv_generation_per_kWp)
print (demand_profile)
cases.mg_fixed(demand_profile, pv_generation_per_kWp)