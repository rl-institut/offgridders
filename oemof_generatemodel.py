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
    def fuel_oem(micro_grid_system, bus_fuel, experiment, total_demand):
        # Does include intended minimal renewable factor
        source_fuel = solph.Source(label="source_fuel",
                                   outputs={bus_fuel: solph.Flow(
                                       variable_costs   = experiment['price_fuel'] / experiment['combustion_value_fuel'],
                                       nominal_value    = (1-experiment['min_res_share']) * total_demand / experiment['genset_efficiency'],
                                       summed_max       = 1
                                   )})
        micro_grid_system.add(source_fuel)
        return micro_grid_system, bus_fuel

    def fuel_fix(micro_grid_system, bus_fuel, experiment):
        # Does NOT include a boundary for intendet minimal renewable factor (as in dispatch, operation costs in focus)
        source_fuel = solph.Source(label="source_fuel",
                                   outputs={bus_fuel: solph.Flow(
                                       variable_costs   = experiment['price_fuel'] / experiment['combustion_value_fuel'])})
        micro_grid_system.add(source_fuel)
        return micro_grid_system, bus_fuel

    def shortage(micro_grid_system, bus_electricity_mg, sum_demand_profile, experiment):
        source_shortage = solph.Source(label="source_shortage",
                                       outputs={bus_electricity_mg: solph.Flow(
                                           variable_costs   = experiment['costs_var_unsupplied_load'],
                                           nominal_value    = experiment['max_share_unsupplied_load'] * sum_demand_profile,
                                           summed_max       = 1)})
        micro_grid_system.add(source_shortage)
        return micro_grid_system, bus_electricity_mg

    def maingrid_consumption(micro_grid_system, bus_electricity_ng, experiment, grid_availability):
        source_maingrid = solph.Source(label="source_maingrid",
                                       outputs={bus_electricity_ng: solph.Flow(
                                           actual_value = grid_availability,
                                           variable_costs=experiment['maingrid_electricity_price'])})
        micro_grid_system.add(source_maingrid)
        return micro_grid_system, bus_electricity_ng
    ######## Sources ########

    ######## Components ########
    def pv_fix(micro_grid_system, bus_electricity_mg, pv_generation_per_kWp, capacity_pv, experiment):
        source_pv = solph.Source(label="source_pv",
                                 outputs={bus_electricity_mg: solph.Flow(label='PV generation',
                                                                         actual_value   = pv_generation_per_kWp,
                                                                         fixed          = True,
                                                                         nominal_value  = capacity_pv,
                                                                         variable_costs = experiment['pv_cost_var']
                                                                         )})

        micro_grid_system.add(source_pv)
        return micro_grid_system, bus_electricity_mg

    def pv_oem(micro_grid_system, bus_electricity_mg, pv_generation_per_kWp, experiment):
        pv_norm = pv_generation_per_kWp / max(pv_generation_per_kWp)
        if pv_norm.any() > 1: logging.warning("Error, PV generation not normalized, greater than 1")
        if pv_norm.any() < 0: logging.warning("Error, PV generation negative")

        source_pv = solph.Source(label="source_pv",
                                 outputs={bus_electricity_mg: solph.Flow(label='PV generation',
                                                                         actual_value=pv_norm,
                                                                         fixed=True,
                                                                         investment=solph.Investment(
                                                                             ep_costs=experiment['pv_cost_annuity']/max(pv_generation_per_kWp)),
                                                                         variable_costs = experiment['pv_cost_var']/max(pv_generation_per_kWp)
                                                                         )})
        micro_grid_system.add(source_pv)
        return micro_grid_system, bus_electricity_mg

    def genset_fix(micro_grid_system, bus_fuel, bus_electricity_mg, capacity_fuel_gen, experiment):
        if experiment['genset_min_loading'] == 0:
            transformer_fuel_generator = solph.Transformer(label="transformer_fuel_generator",
                                                           inputs={bus_fuel: solph.Flow()},
                                                           outputs={bus_electricity_mg: solph.Flow(
                                                               nominal_value=capacity_fuel_gen,
                                                               variable_costs=experiment['genset_cost_var'])},
                                                           conversion_factors={
                                                               bus_electricity_mg: experiment['genset_efficiency']}
                                                           )
        else:
            transformer_fuel_generator = solph.Transformer(label="transformer_fuel_generator",
                                                       inputs   ={bus_fuel: solph.Flow()},
                                                       outputs  ={bus_electricity_mg: solph.Flow(
                                                           nominal_value    = capacity_fuel_gen,
                                                           variable_costs   = experiment['genset_cost_var'],
                                                           min=experiment['genset_min_loading'],
                                                           max=experiment['genset_max_loading'],
                                                           nonconvex=solph.NonConvex())},
                                                       conversion_factors={ bus_electricity_mg: experiment['genset_efficiency']}
                                                       )

        micro_grid_system.add(transformer_fuel_generator)
        return micro_grid_system, bus_fuel, bus_electricity_mg

    def genset_oem(micro_grid_system, bus_fuel, bus_electricity_mg, experiment):
        transformer_fuel_generator = solph.Transformer(label="transformer_fuel_generator",
                                                       inputs={bus_fuel: solph.Flow()},
                                                       outputs={bus_electricity_mg: solph.Flow(
                                                           investment=solph.Investment(
                                                               ep_costs=experiment['genset_cost_annuity']),
                                                           variable_costs=experiment['genset_cost_var'])},
                                                       conversion_factors={bus_electricity_mg: experiment['genset_efficiency']})
        micro_grid_system.add(transformer_fuel_generator)
        return micro_grid_system, bus_fuel, bus_electricity_mg

    def pointofcoupling_feedin_fix(micro_grid_system, bus_electricity_mg, bus_electricity_ng, capacity_pointofcoupling, experiment):
        pointofcoupling = solph.Transformer(label="transformer_pcc_feedin",
                                                       inputs={bus_electricity_mg: solph.Flow()},
                                                       outputs={bus_electricity_ng: solph.Flow(
                                                           nominal_value=capacity_pointofcoupling,
                                                           variable_costs=experiment['pcoupling_cost_var'])},
                                                       conversion_factors={
                                                           bus_electricity_mg: experiment['pcoupling_efficiency']})  # is efficiency of the generator?? Then this should later on be included as a function of the load factor

        micro_grid_system.add(pointofcoupling)
        return micro_grid_system, bus_electricity_mg, bus_electricity_ng

    # todo point of coupling = max(demand) limits PV feed-in, therefore there should be a minimal pcc capacity defined with
    # optimal larger size though OEM. existing = min_cap_pointofcoupling. but are all costs included?
    # ERROR-Optimization failed with status ok and terminal condition unbounded when using existing = min_cap_pointofcoupling
    def pointofcoupling_feedin_oem(micro_grid_system, bus_electricity_mg, bus_electricity_ng, min_cap_pointofcoupling, experiment):
        pointofcoupling = solph.Transformer(label="transformer_pcc_feedin",
                                                       inputs={bus_electricity_mg: solph.Flow()},
                                                       outputs={bus_electricity_ng: solph.Flow(
                                                           investment=solph.Investment(
                                                               ep_costs=experiment['pcoupling_cost_annuity']),
                                                           variable_costs=experiment['pcoupling_cost_var'])},
                                                       conversion_factors={bus_electricity_mg: experiment['pcoupling_efficiency']})
        micro_grid_system.add(pointofcoupling)
        return micro_grid_system, bus_electricity_mg, bus_electricity_ng

    def pointofcoupling_consumption_fix(micro_grid_system, bus_electricity_mg, bus_electricity_ng, cap_pointofcoupling, experiment):
        pointofcoupling = solph.Transformer(label="transformer_pcc_consumption",
                                                       inputs={bus_electricity_ng: solph.Flow()},
                                                       outputs={bus_electricity_mg: solph.Flow(
                                                           nominal_value=cap_pointofcoupling,
                                                           variable_costs=experiment['pcoupling_cost_var'])},
                                                       conversion_factors={
                                                           bus_electricity_mg: experiment['pcoupling_efficiency']})  # is efficiency of the generator?? Then this should later on be included as a function of the load factor

        micro_grid_system.add(pointofcoupling)
        return micro_grid_system, bus_electricity_mg, bus_electricity_ng

    def pointofcoupling_consumption_oem(micro_grid_system, bus_electricity_mg, bus_electricity_ng, experiment):
        pointofcoupling = solph.Transformer(label="transformer_pcc_consumption",
                                                       inputs={bus_electricity_ng: solph.Flow()},
                                                       outputs={bus_electricity_mg: solph.Flow(
                                                           investment=solph.Investment(
                                                               ep_costs=experiment['pcoupling_cost_annuity']),
                                                           variable_costs=experiment['pcoupling_cost_var'])},
                                                       conversion_factors={bus_electricity_mg: experiment['pcoupling_efficiency']})
        micro_grid_system.add(pointofcoupling)
        return micro_grid_system, bus_electricity_mg, bus_electricity_ng

    def storage_fix(micro_grid_system, bus_electricity_mg, capacity_storage, experiment):
        generic_storage = solph.components.GenericStorage(
            label                       = 'generic_storage',
            nominal_capacity            = capacity_storage,
            inputs={bus_electricity_mg: solph.Flow(
                nominal_value= capacity_storage*experiment['storage_Crate']
                )},  # maximum charge possible in one timestep
            outputs={bus_electricity_mg: solph.Flow(
                nominal_value= capacity_storage*experiment['storage_Crate'],
                variable_costs=experiment['storage_cost_var']
                )},  # maximum discharge possible in one timestep
            capacity_loss               = experiment['storage_loss_timestep'],  # from timestep to timestep
            capacity_min                = experiment['storage_capacity_min'],
            capacity_max                = experiment['storage_capacity_max'],
            initial_capacity            = experiment['storage_initial_soc'],  # in terms of SOC?
            inflow_conversion_factor    = experiment['storage_inflow_efficiency'],  # storing efficiency
            outflow_conversion_factor   = experiment['storage_outflow_efficiency'])  # efficiency of discharge
        micro_grid_system.add(generic_storage)
        return micro_grid_system, bus_electricity_mg

    def storage_oem(micro_grid_system, bus_electricity_mg, experiment):
        generic_storage = solph.components.GenericStorage(
            label='generic_storage',
            investment=solph.Investment(ep_costs=experiment['storage_cost_annuity']),
            inputs                          = {bus_electricity_mg: solph.Flow()},
            outputs                         = {bus_electricity_mg: solph.Flow(
                variable_costs=experiment['storage_cost_var'])},
            capacity_loss                   = experiment['storage_loss_timestep'],  # from timestep to timestep
            capacity_min                    = experiment['storage_capacity_min'],
            capacity_max                    = experiment['storage_capacity_max'],
            inflow_conversion_factor        = experiment['storage_inflow_efficiency'],  # storing efficiency
            outflow_conversion_factor       = experiment['storage_outflow_efficiency'],  # efficiency of discharge
            invest_relation_input_capacity  = experiment['storage_Crate'],  # storage can be charged with invest_relation_output_capacity*capacity in one timeperiod
            invest_relation_output_capacity = experiment['storage_Crate'] # storage can be emptied with invest_relation_output_capacity*capacity in one timeperiod
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

    def maingrid_feedin(micro_grid_system, bus_electricity_ng, experiment, grid_availability):
        # create and add demand sink to micro_grid_system - fixed
        sink_feedin_ng = solph.Sink(label="sink_feedin",
                                 inputs={bus_electricity_ng: solph.Flow(
                                     actual_value=grid_availability,
                                     variable_costs = - experiment['maingrid_feedin_tariff'])})
        micro_grid_system.add(sink_feedin_ng)
        return micro_grid_system, bus_electricity_ng
    ######## Sinks ########