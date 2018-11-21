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
    def fuel_oem(micro_grid_system, bus_fuel, experiment, total_demand):
        source_fuel = solph.Source(label="source_fuel",
                                   outputs={bus_fuel: solph.Flow(
                                       variable_costs   = experiment['price_fuel'] / experiment['combustion_value_fuel'],
                                       nominal_value    = (1-experiment['min_res_share']) * total_demand / experiment['genset_efficiency'],
                                       summed_max       = 1
                                   )})
        micro_grid_system.add(source_fuel)
        return micro_grid_system, bus_fuel

    def fuel_fix(micro_grid_system, bus_fuel, experiment):
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

    def maingrid(micro_grid_system, bus_electricity_ng, price_electricity_main_grid, experiment):
        source_maingrid = solph.Source(label="source_maingrid",
                                       outputs={bus_electricity_ng: solph.Flow(
                                           variable_costs=experiment['price_electricity_main_grid'])})
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
                                                                         variable_costs=experiment['cost_var_pv']
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
                                                                             ep_costs=experiment['cost_annuity_pv']),
                                                                         variable_costs = experiment['cost_var_pv']/max(pv_generation_per_kWp)
                                                                         )})
        micro_grid_system.add(source_pv)
        return micro_grid_system, bus_electricity_mg

    # todo: edit so that nonconvex flow can be used. => enormeous computing time in fixed version
    # todo: problems with min=0?
    # todo: implement offset generator?
    def genset_fix(micro_grid_system, bus_fuel, bus_electricity_mg, capacity_fuel_gen, experiment):
        transformer_fuel_generator = solph.Transformer(label="transformer_fuel_generator",
                                                       inputs   ={bus_fuel: solph.Flow()},
                                                       outputs  ={bus_electricity_mg: solph.Flow(
                                                           nominal_value    = capacity_fuel_gen,
                                                           variable_costs   = experiment['cost_var_genset'],
                                                           min=experiment['genset_min_loading'],
                                                           max=experiment['genset_max_loading'],
                                                           nonconvex=solph.NonConvex())},
                                                       conversion_factors={ bus_electricity_mg: experiment['genset_efficiency']}
                                                       )  # is efficiency of the generator?? Then this should later on be included as a function of the load factor

        micro_grid_system.add(transformer_fuel_generator)
        return micro_grid_system, bus_fuel, bus_electricity_mg

    def genset_oem(micro_grid_system, bus_fuel, bus_electricity_mg, experiment):
        transformer_fuel_generator = solph.Transformer(label="transformer_fuel_generator",
                                                       inputs={bus_fuel: solph.Flow()},
                                                       outputs={bus_electricity_mg: solph.Flow(
                                                           investment=solph.Investment(
                                                               ep_costs=experiment['cost_annuity_genset']),
                                                           variable_costs=experiment['cost_var_genset'])},
                                                       conversion_factors={bus_electricity_mg: experiment['genset_efficiency']})
        micro_grid_system.add(transformer_fuel_generator)
        return micro_grid_system, bus_fuel, bus_electricity_mg

    def pointofcoupling_feedin_fix(micro_grid_system, bus_electricity_mg, bus_electricity_ng, capacity_pointofcoupling, experiment):
        pointofcoupling = solph.Transformer(label="transformer_pointofcoupling_feedin",
                                                       inputs={bus_electricity_mg: solph.Flow()},
                                                       outputs={bus_electricity_ng: solph.Flow(
                                                           nominal_value=capacity_pointofcoupling,
                                                           variable_costs=experiment['cost_var_pcoupling'])},
                                                       conversion_factors={
                                                           bus_electricity_mg: experiment['efficiency_pcoupling']})  # is efficiency of the generator?? Then this should later on be included as a function of the load factor

        micro_grid_system.add(pointofcoupling)
        return micro_grid_system, bus_electricity_mg, bus_electricity_ng

    def pointofcoupling_feedin_oem(micro_grid_system, bus_electricity_mg, bus_electricity_ng, experiment):
        pointofcoupling = solph.Transformer(label="transformer_pointofcoupling_feedin",
                                                       inputs={bus_electricity_mg: solph.Flow()},
                                                       outputs={bus_electricity_ng: solph.Flow(
                                                           investment=solph.Investment(
                                                               ep_costs=experiment['cost_annuity_pcoupling']),
                                                           variable_costs=experiment['cost_var_pcoupling'])},
                                                       conversion_factors={bus_electricity_mg: experiment['efficiency_pcoupling']})
        micro_grid_system.add(pointofcoupling)
        return micro_grid_system, bus_electricity_mg, bus_electricity_ng

    def pointofcoupling_tomg_fix(micro_grid_system, bus_electricity_mg, bus_electricity_ng, cap_pointofcoupling, experiment):
        pointofcoupling = solph.Transformer(label="transformer_pointofcoupling_tomg",
                                                       inputs={bus_electricity_ng: solph.Flow()},
                                                       outputs={bus_electricity_mg: solph.Flow(
                                                           nominal_value=cap_pointofcoupling,
                                                           variable_costs=experiment['cost_var_pcoupling'])},
                                                       conversion_factors={
                                                           bus_electricity_mg: experiment['efficiency_pcoupling']})  # is efficiency of the generator?? Then this should later on be included as a function of the load factor

        micro_grid_system.add(pointofcoupling)
        return micro_grid_system, bus_electricity_mg, bus_electricity_ng

    def pointofcoupling_tomg_oem(micro_grid_system, bus_electricity_mg, bus_electricity_ng, experiment):
        pointofcoupling = solph.Transformer(label="transformer_pointofcoupling_tomg",
                                                       inputs={bus_electricity_ng: solph.Flow()},
                                                       outputs={bus_electricity_mg: solph.Flow(
                                                           investment=solph.Investment(
                                                               ep_costs=experiment['cost_annuity_pcoupling']),
                                                           variable_costs=experiment['cost_var_pcoupling'])},
                                                       conversion_factors={bus_electricity_mg: experiment['efficiency_pcoupling']})
        micro_grid_system.add(pointofcoupling)
        return micro_grid_system, bus_electricity_mg, bus_electricity_ng

    def storage_fix(micro_grid_system, bus_electricity_mg, capacity_storage, experiment):
        generic_storage = solph.components.GenericStorage(
            label                       = 'generic_storage',
            nominal_capacity            = capacity_storage,
            inputs={bus_electricity_mg: solph.Flow(
                nominal_value= capacity_storage*experiment['storage_Crate'],
                variable_costs=experiment['cost_var_storage']
                )},  # maximum charge possible in one timestep
            outputs={bus_electricity_mg: solph.Flow(
                nominal_value= capacity_storage*experiment['storage_Crate'],
                variable_costs=experiment['cost_var_storage']
                )},  # maximum discharge possible in one timestep
            capacity_loss               = experiment['storage_loss_timestep'],  # from timestep to timestep
            capacity_min                = experiment['storage_capacity_min'],
            capacity_max                = experiment['storage_capacity_max'],
            initial_capacity            = experiment['storage_initial_soc'],  # in terms of SOC? # todo check this point
            inflow_conversion_factor    = experiment['storage_inflow_efficiency'],  # storing efficiency
            outflow_conversion_factor   = experiment['storage_outflow_efficiency'])  # efficiency of discharge
        micro_grid_system.add(generic_storage)
        return micro_grid_system, bus_electricity_mg

    def storage_oem(micro_grid_system, bus_electricity_mg, experiment):
        generic_storage = solph.components.GenericStorage(
            label='generic_storage',
            investment=solph.Investment(ep_costs=experiment['cost_annuity_storage']),
            inputs                          = {bus_electricity_mg: solph.Flow()},
            outputs                         = {bus_electricity_mg: solph.Flow(
                variable_costs=experiment['cost_var_storage'])},
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

    def feedin(micro_grid_system, bus_electricity_ng):
        # create and add demand sink to micro_grid_system - fixed
        sink_feedin_ng = solph.Sink(label="sink_feedin",
                                 inputs={bus_electricity_ng: solph.Flow()})
        micro_grid_system.add(sink_feedin_ng)
        return micro_grid_system, bus_electricity_ng
    ######## Sinks ########