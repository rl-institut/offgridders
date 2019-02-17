"""
Requires:
oemof, matplotlib, demandlib, pvlib
tables, tkinter
"""

###############################################################################
# Imports and initialize
###############################################################################

import oemof.solph as solph
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

class generate():
    ######## Sources ########
    def fuel_oem(micro_grid_system, bus_fuel, experiment):
        logging.debug('Added to oemof model: source fuel oem')
        # Does include intended minimal renewable factor as total max for fuel consumption -> just do decrease horizon
        # of possible solutions
        # i would delete this criterion here, if i add an additional constraint
        source_fuel = solph.Source(label="source_fuel",
                                   outputs={bus_fuel: solph.Flow(
                                       variable_costs   = experiment['price_fuel'] / experiment['combustion_value_fuel'],
                                       nominal_value    = (1-experiment['min_renewable_share']) * experiment['total_demand'] / experiment['genset_efficiency'],
                                       summed_max       = 1
                                   )})
        micro_grid_system.add(source_fuel)
        return

    def fuel_fix(micro_grid_system, bus_fuel, experiment):
        logging.debug('Added to oemof model: source fuel fix')
        # Does NOT include a boundary for intendet minimal renewable factor (as in dispatch, operation costs in focus)
        source_fuel = solph.Source(label="source_fuel",
                                   outputs={bus_fuel: solph.Flow(
                                       variable_costs   = experiment['price_fuel'] / experiment['combustion_value_fuel'])})
        micro_grid_system.add(source_fuel)
        return

    def shortage(micro_grid_system, bus_electricity_mg, experiment, case_dict):
        logging.debug('Added to oemof model: source shortage')
        source_shortage = solph.Source(label="source_shortage",
                                       outputs={bus_electricity_mg: solph.Flow(
                                           variable_costs   = experiment['costs_var_unsupplied_load'],
                                           nominal_value    = case_dict['max_shortage'] * case_dict['total_demand'],
                                           summed_max       = 1)})
        micro_grid_system.add(source_shortage)
        return source_shortage

    def maingrid_consumption(micro_grid_system, experiment):
        logging.debug('Added to oemof model: maingrid consumption')
        # create and add demand sink to micro_grid_system - fixed
        bus_electricity_ng_consumption = solph.Bus(label="bus_electricity_ng_consumption")
        micro_grid_system.add(bus_electricity_ng_consumption)

        source_maingrid_consumption = solph.Source(label="source_maingrid_consumption",
                                       outputs={bus_electricity_ng_consumption: solph.Flow(
                                           actual_value = experiment['grid_availability'],
                                           fixed = True,
                                           investment = solph.Investment(ep_costs=0)
                                           )})

        micro_grid_system.add(source_maingrid_consumption)

        sink_maingrid_consumption_symbolic = solph.Sink(label="sink_maingrid_consumption_symbolic",
                                 inputs={bus_electricity_ng_consumption: solph.Flow()})
        micro_grid_system.add(sink_maingrid_consumption_symbolic)
        return bus_electricity_ng_consumption
    ######## Sources ########

    ######## Components ########
    def pv_fix(micro_grid_system, bus_electricity_mg, experiment, capacity_pv):
        logging.debug('Added to oemof model: pv fix')
        source_pv = solph.Source(label="source_pv",
                                 outputs={bus_electricity_mg: solph.Flow(label='PV generation',
                                                                         actual_value   = experiment['pv_generation_per_kWp'],
                                                                         fixed          = True,
                                                                         nominal_value  = capacity_pv,
                                                                         variable_costs = experiment['pv_cost_var']
                                                                         )})

        micro_grid_system.add(source_pv)
        return source_pv

    def pv_oem(micro_grid_system, bus_electricity_mg, experiment):
        logging.debug('Added to oemof model: pv oem')
        peak_pv_generation = experiment['peak_pv_generation_per_kWp']
        pv_norm = experiment['pv_generation_per_kWp'] / peak_pv_generation
        if pv_norm.any() > 1: logging.warning("Error, PV generation not normalized, greater than 1")
        if pv_norm.any() < 0: logging.warning("Error, PV generation negative")

        source_pv = solph.Source(label="source_pv",
                                 outputs={bus_electricity_mg: solph.Flow(label='PV generation',
                                                                         actual_value=pv_norm,
                                                                         fixed=True,
                                                                         investment=solph.Investment(
                                                                             ep_costs=experiment['pv_cost_annuity']/peak_pv_generation),
                                                                         variable_costs = experiment['pv_cost_var']/peak_pv_generation
                                                                         )})
        micro_grid_system.add(source_pv)
        return source_pv

    ######## Components ########
    def wind_fix(micro_grid_system, bus_electricity_mg, experiment, capacity_wind):
        logging.debug('Added to oemof model: wind')
        source_wind = solph.Source(label="source_wind",
                                 outputs={bus_electricity_mg: solph.Flow(label='Wind generation',
                                                                         actual_value   = experiment['wind_generation_per_kW'],
                                                                         fixed          = True,
                                                                         nominal_value  = capacity_wind,
                                                                         variable_costs = experiment['wind_cost_var']
                                                                         )})

        micro_grid_system.add(source_wind)
        return source_wind

    def wind_oem(micro_grid_system, bus_electricity_mg, experiment):
        logging.debug('Added to oemof model: wind')
        peak_wind_generation = experiment['peak_wind_generation_per_kW']
        wind_norm = experiment['wind_generation_per_kW'] / peak_wind_generation
        if wind_norm.any() > 1: logging.warning("Error, Wind generation not normalized, greater than 1")
        if wind_norm.any() < 0: logging.warning("Error, Wind generation negative")

        source_wind = solph.Source(label="source_wind",
                                 outputs={bus_electricity_mg: solph.Flow(label='Wind generation',
                                                                         actual_value=wind_norm,
                                                                         fixed=True,
                                                                         investment=solph.Investment(
                                                                             ep_costs=experiment['wind_cost_annuity']/peak_wind_generation),
                                                                         variable_costs = experiment['wind_cost_var']/peak_wind_generation
                                                                         )})
        micro_grid_system.add(source_wind)
        return source_wind

    def genset_fix(micro_grid_system, bus_fuel, bus_electricity_mg, experiment, capacity_fuel_gen, number_of_equal_generators):
        logging.debug('Added to oemof model: genset fix no minload')
        dict_of_generators = {}
        for number in range(1, number_of_equal_generators + 1):
            genset = solph.Transformer(label="transformer_genset_"+ str(number),
                                                       inputs={bus_fuel: solph.Flow()},
                                                       outputs={bus_electricity_mg: solph.Flow(
                                                           nominal_value=capacity_fuel_gen / number_of_equal_generators,
                                                           variable_costs=experiment['genset_cost_var'])},
                                                       conversion_factors={
                                                           bus_electricity_mg: experiment['genset_efficiency']}
                                                       )
            micro_grid_system.add(genset)
            dict_of_generators.update({number: genset})
        return dict_of_generators

    def genset_fix_minload(micro_grid_system, bus_fuel, bus_electricity_mg, experiment, capacity_fuel_gen, number_of_equal_generators):
        logging.debug('Added to oemof model: genset fix minload')
        dict_of_generators = {}
        for number in range(1, number_of_equal_generators +1):
            genset = solph.Transformer(label="transformer_genset_"+ str(number),
                                                       inputs   ={bus_fuel: solph.Flow()},
                                                       outputs  ={bus_electricity_mg: solph.Flow(
                                                           nominal_value    = capacity_fuel_gen/number_of_equal_generators,
                                                           variable_costs   = experiment['genset_cost_var'],
                                                           min=experiment['genset_min_loading'],
                                                           max=experiment['genset_max_loading'],
                                                           nonconvex=solph.NonConvex())},
                                                       conversion_factors={ bus_electricity_mg: experiment['genset_efficiency']}
                                                       )
            micro_grid_system.add(genset)
            dict_of_generators.update({number: genset})

        return dict_of_generators

    def genset_oem(micro_grid_system, bus_fuel, bus_electricity_mg, experiment, number_of_generators):
        logging.debug('Added to oemof model: genset oem no minload')
        dict_of_generators = {}
        for number in range(1, number_of_generators + 1):
            genset = solph.Transformer(label="transformer_genset_"+ str(number),
                                                           inputs={bus_fuel: solph.Flow()},
                                                           outputs={bus_electricity_mg: solph.Flow(
                                                               investment=solph.Investment(
                                                                   ep_costs=experiment['genset_cost_annuity']),
                                                               variable_costs=experiment['genset_cost_var'])},
                                                           conversion_factors={bus_electricity_mg: experiment['genset_efficiency']})
            micro_grid_system.add(genset)
            dict_of_generators.update({number: genset})
        return dict_of_generators

    def genset_oem_minload(micro_grid_system, bus_fuel, bus_electricity_mg, experiment):
        logging.debug('Added to oemof model: genset oem minload')
        logging.warning('Currently not possible to optimize capacities of generator with minimal loading with OEMOF!')
        genset = solph.Transformer(label="transformer_genset",
                                                   inputs   ={bus_fuel: solph.Flow()},
                                                   outputs  ={bus_electricity_mg: solph.Flow(
                                                       investment=solph.Investment(
                                                           ep_costs=experiment['genset_cost_annuity']),
                                                       variable_costs   = experiment['genset_cost_var'],
                                                       min=experiment['genset_min_loading'],
                                                       max=experiment['genset_max_loading'],
                                                       nonconvex=solph.NonConvex())},
                                                   conversion_factors={ bus_electricity_mg: experiment['genset_efficiency']}
                                                   )
        micro_grid_system.add(genset)
        return genset

    def pointofcoupling_feedin_fix(micro_grid_system, bus_electricity_mg, bus_electricity_ng_feedin, experiment, capacity_pointofcoupling):
        logging.debug('Added to oemof model: pcc feedin fix')
        pointofcoupling_feedin = solph.Transformer(label="transformer_pcc_feedin",
                                                       inputs={bus_electricity_mg: solph.Flow(
                                                           nominal_value=capacity_pointofcoupling,
                                                           variable_costs=experiment['pcoupling_cost_var']-experiment['maingrid_feedin_tariff']
                                                       )},
                                                       outputs={bus_electricity_ng_feedin: solph.Flow()},
                                                       conversion_factors={
                                                           bus_electricity_mg: experiment['pcoupling_efficiency']})  # is efficiency of the generator?? Then this should later on be included as a function of the load factor

        micro_grid_system.add(pointofcoupling_feedin)
        return

    # point of coupling = max(demand) limits PV feed-in, therefore there should be a minimal pcc capacity defined with
    # optimal larger size though OEM. existing = min_cap_pointofcoupling. but are all costs included?
    def pointofcoupling_feedin_oem(micro_grid_system, bus_electricity_mg, bus_electricity_ng_feedin, experiment, min_cap_pointofcoupling):
        logging.debug('Added to oemof model: pcc feedin oem')
        pointofcoupling_feedin = solph.Transformer(label="transformer_pcc_feedin",
                                                       inputs={bus_electricity_mg: solph.Flow(
                                                           investment=solph.Investment(
                                                               ep_costs=experiment['pcoupling_cost_annuity']),
                                                           variable_costs=experiment['pcoupling_cost_var']-experiment['maingrid_feedin_tariff']
                                                       )},
                                                       outputs={bus_electricity_ng_feedin: solph.Flow()},
                                                       conversion_factors={bus_electricity_mg: experiment['pcoupling_efficiency']})
        micro_grid_system.add(pointofcoupling_feedin)
        return

    def pointofcoupling_consumption_fix(micro_grid_system, bus_electricity_mg, bus_electricity_ng_consumption, experiment, cap_pointofcoupling):
        logging.debug('Added to oemof model: pcc consumption fix')
        pointofcoupling_consumption = solph.Transformer(label="transformer_pcc_consumption",
                                                       inputs={bus_electricity_ng_consumption: solph.Flow(
                                                           nominal_value=cap_pointofcoupling, # inflow is limited to nominal value!
                                                           variable_costs = experiment['pcoupling_cost_var']+experiment['maingrid_electricity_price'],                                                       )},
                                                       outputs={bus_electricity_mg: solph.Flow()},
                                                       conversion_factors={
                                                           bus_electricity_ng_consumption: experiment['pcoupling_efficiency']})  # is efficiency of the generator?? Then this should later on be included as a function of the load factor

        micro_grid_system.add(pointofcoupling_consumption)
        return pointofcoupling_consumption

    def pointofcoupling_consumption_oem(micro_grid_system, bus_electricity_mg, bus_electricity_ng_consumption, experiment, min_cap_pointofcoupling):
        logging.debug('Added to oemof model: pcc consumption oem')
        pointofcoupling_consumption = solph.Transformer(label="transformer_pcc_consumption",
                                                       inputs={bus_electricity_ng_consumption: solph.Flow(
                                                           variable_costs=experiment['pcoupling_cost_var']+experiment['maingrid_electricity_price'],
                                                           investment=solph.Investment(
                                                               ep_costs=experiment['pcoupling_cost_annuity'])
                                                       )},
                                                       outputs={bus_electricity_mg: solph.Flow()},
                                                       conversion_factors={bus_electricity_ng_consumption: experiment['pcoupling_efficiency']})
        micro_grid_system.add(pointofcoupling_consumption)
        return pointofcoupling_consumption

    def storage_fix(micro_grid_system, bus_electricity_mg, experiment, capacity_storage):
        logging.debug('Added to oemof model: storage fix')
        generic_storage = solph.components.GenericStorage(
            label                       = 'generic_storage',
            nominal_capacity            = capacity_storage,
            inputs={bus_electricity_mg: solph.Flow(
                nominal_value= capacity_storage*experiment['storage_Crate_charge'],
                variable_costs=experiment['storage_cost_var']
                )},  # maximum charge possible in one timestep
            outputs={bus_electricity_mg: solph.Flow(
                nominal_value= capacity_storage*experiment['storage_Crate_discharge']
                )},  # maximum discharge possible in one timestep
            capacity_loss               = experiment['storage_loss_timestep'],  # from timestep to timestep
            capacity_min                = experiment['storage_capacity_min'],
            capacity_max                = experiment['storage_capacity_max'],
            initial_capacity            = experiment['storage_initial_soc'],  # in terms of SOC?
            inflow_conversion_factor    = experiment['storage_inflow_efficiency'],  # storing efficiency
            outflow_conversion_factor   = experiment['storage_outflow_efficiency'])  # efficiency of discharge
        micro_grid_system.add(generic_storage)
        return generic_storage

    def storage_oem(micro_grid_system, bus_electricity_mg, experiment):
        logging.debug('Added to oemof model: storage oem')
        generic_storage = solph.components.GenericStorage(
            label='generic_storage',
            investment=solph.Investment(ep_costs=experiment['storage_cost_annuity']),
            inputs                          = {bus_electricity_mg: solph.Flow(
                variable_costs=experiment['storage_cost_var'])},
            outputs                         = {bus_electricity_mg: solph.Flow()},
            capacity_loss                   = experiment['storage_loss_timestep'],  # from timestep to timestep
            capacity_min                    = experiment['storage_capacity_min'],
            capacity_max                    = experiment['storage_capacity_max'],
            inflow_conversion_factor        = experiment['storage_inflow_efficiency'],  # storing efficiency
            outflow_conversion_factor       = experiment['storage_outflow_efficiency'],  # efficiency of discharge
            invest_relation_input_capacity  = experiment['storage_Crate_charge'],  # storage can be charged with invest_relation_output_capacity*capacity in one timeperiod
            invest_relation_output_capacity = experiment['storage_Crate_discharge'] # storage can be emptied with invest_relation_output_capacity*capacity in one timeperiod
        )
        micro_grid_system.add(generic_storage)
        return generic_storage
    ######## Components ########

    ######## Sinks ########
    def excess(micro_grid_system, bus_electricity_mg):
        logging.debug('Added to oemof model: excess')
        # create and add excess electricity sink to micro_grid_system - variable
        sink_excess = solph.Sink(label="sink_excess",
                                 inputs={bus_electricity_mg: solph.Flow()})
        micro_grid_system.add(sink_excess)
        return

    def demand(micro_grid_system, bus_electricity_mg, demand_profile):
        logging.debug('Added to oemof model: demand')
        # create and add demand sink to micro_grid_system - fixed
        sink_demand = solph.Sink(label="sink_demand",
                                 inputs={bus_electricity_mg: solph.Flow(
                                     actual_value=demand_profile,
                                     nominal_value=1,
                                     fixed=True)})
        micro_grid_system.add(sink_demand)
        return sink_demand

    def maingrid_feedin(micro_grid_system, experiment):
        logging.debug('Added to oemof model: maingrid feedin')
        bus_electricity_ng_feedin = solph.Bus(label="bus_electricity_ng_feedin")
        micro_grid_system.add(bus_electricity_ng_feedin)

        # create and add demand sink to micro_grid_system - fixed
        sink_maingrid_feedin = solph.Sink(label="sink_maingrid_feedin",
                                 inputs={bus_electricity_ng_feedin: solph.Flow(
                                     actual_value = experiment['grid_availability'],
                                     fixed = True,
                                     investment=solph.Investment(ep_costs=0))})
        micro_grid_system.add(sink_maingrid_feedin)

        # to fill in for not really provided feed in
        source_maingrid_feedin_symbolic = solph.Source(label="source_maingrid_feedin_symbolic",
                                       outputs={bus_electricity_ng_feedin: solph.Flow()})
        micro_grid_system.add(source_maingrid_feedin_symbolic)
        return bus_electricity_ng_feedin

    ######## Sinks ########