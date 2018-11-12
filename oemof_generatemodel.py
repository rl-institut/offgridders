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

    def maingrid(micro_grid_system, bus_electricity_ng):
        from config import maingrid_electricity_costs
        source_maingrid = solph.Source(label="source_shortage",
                                       outputs={bus_electricity_ng: solph.Flow(
                                           variable_costs=maingrid_electricity_costs)})
        micro_grid_system.add(source_maingrid)
        return micro_grid_system, bus_electricity_ng
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

    def genset_fix(micro_grid_system, bus_fuel, bus_electricity_mg):
        from input_values import cap_fuel_gen
        transformer_fuel_generator = solph.Transformer(label="transformer_fuel_generator",
                                                       inputs={bus_fuel: solph.Flow()},
                                                       outputs={bus_electricity_mg: solph.Flow(
                                                           nominal_value=cap_fuel_gen)},
                                                       conversion_factors={
                                                           bus_electricity_mg: 0.58})  # is efficiency of the generator?? Then this should later on be included as a function of the load factor

        micro_grid_system.add(transformer_fuel_generator)
        return micro_grid_system, bus_fuel, bus_electricity_mg

    def genset_oem(micro_grid_system, bus_fuel, bus_electricity_mg):
        from input_values import cost_data
        transformer_fuel_generator = solph.Transformer(label="transformer_fuel_generator",
                                                       inputs={bus_fuel: solph.Flow()},
                                                       outputs={bus_electricity_mg: solph.Flow(
                                                           investment=solph.Investment(
                                                               ep_costs=cost_data.loc['annuity', 'GenSet']))},
                                                       conversion_factors={bus_electricity_mg: 0.58})
        micro_grid_system.add(transformer_fuel_generator)
        return micro_grid_system, bus_fuel, bus_electricity_mg

    def pointofcoupling_feedin(micro_grid_system, bus_electricity_mg, bus_electricity_ng):
        from input_values import cap_fuel_gen
        pointofcoupling = solph.Transformer(label="transformer_fuel_generator",
                                                       inputs={bus_electricity_mg: solph.Flow()},
                                                       outputs={bus_electricity_ng: solph.Flow(
                                                           nominal_value=cap_pointofcoupling)},
                                                       conversion_factors={
                                                           bus_electricity_mg: 0.98})  # is efficiency of the generator?? Then this should later on be included as a function of the load factor

        micro_grid_system.add(pointofcoupling)
        return micro_grid_system, bus_electricity_mg, bus_electricity_ng

    def pointofcoupling_feedin(micro_grid_system, bus_electricity_mg, bus_electricity_ng):
        from input_values import cost_data
        pointofcoupling = solph.Transformer(label="transformer_fuel_generator",
                                                       inputs={bus_electricity_mg: solph.Flow()},
                                                       outputs={bus_electricity_ng: solph.Flow(
                                                           investment=solph.Investment(
                                                               ep_costs=cost_data.loc['annuity', 'PC']))},
                                                       conversion_factors={bus_electricity_mg: 0.98})
        micro_grid_system.add(pointofcoupling)
        return micro_grid_system, bus_electricity_mg, bus_electricity_ng

    def pointofcoupling_tomg(micro_grid_system, bus_electricity_mg, bus_electricity_ng):
        from input_values import cap_fuel_gen
        pointofcoupling = solph.Transformer(label="transformer_fuel_generator",
                                                       inputs={bus_electricity_ng: solph.Flow()},
                                                       outputs={bus_electricity_mg: solph.Flow(
                                                           nominal_value=cap_pointofcoupling)},
                                                       conversion_factors={
                                                           bus_electricity_mg: 0.98})  # is efficiency of the generator?? Then this should later on be included as a function of the load factor

        micro_grid_system.add(pointofcoupling)
        return micro_grid_system, bus_electricity_mg, bus_electricity_ng

    def pointofcoupling_tomg(micro_grid_system, bus_electricity_mg, bus_electricity_ng):
        from input_values import cost_data
        pointofcoupling = solph.Transformer(label="transformer_fuel_generator",
                                                       inputs={bus_electricity_ng: solph.Flow()},
                                                       outputs={bus_electricity_mg: solph.Flow(
                                                           investment=solph.Investment(
                                                               ep_costs=cost_data.loc['annuity', 'PC']))},
                                                       conversion_factors={bus_electricity_mg: 0.98})
        micro_grid_system.add(pointofcoupling)
        return micro_grid_system, bus_electricity_mg, bus_electricity_ng

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

    def feedin(micro_grid_system, bus_electricity_ng):
        # create and add demand sink to micro_grid_system - fixed
        sink_feedin_ng = solph.Sink(label="sink_demand",
                                 inputs={bus_electricity_ng: solph.Flow()})
        micro_grid_system.add(sink_feedin_ng)
        return micro_grid_system, bus_electricity_ng
    ######## Sinks ########