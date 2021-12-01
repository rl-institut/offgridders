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
import matplotlib.pyplot as plt

from src.constants import (
    SOURCE_FUEL,
    PRICE_FUEL,
    COMBUSTION_VALUE_FUEL,
    SOURCE_SHORTAGE,
    SHORTAGE_PENALTY_COST,
    MAX_SHORTAGE,
    TOTAL_DEMAND_AC,
    TOTAL_DEMAND_DC,
    BUS_ELECTRICITY_NG_CONSUMPTION,
    SOURCE_MAINGRID_CONSUMPTION,
    SINK_MAINGRID_CONSUMPTION_SYMBOLIC,
    SOURCE_PV,
    PV_GENERATION_PER_KWP,
    PV_COST_VAR,
    PEAK_PV_GENERATION_PER_KWP,
    PV_COST_ANNUITY,
    SOURCE_WIND,
    WIND_GENERATION_PER_KW,
    WIND_COST_VAR,
    PEAK_WIND_GENERATION_PER_KW,
    RECTIFIER_AC_DC_COST_VAR,
    RECTIFIER_AC_DC_EFFICIENCY,
    RECTIFIER_AC_DC_COST_ANNUITY,
    INVERTER_DC_AC_COST_VAR,
    INVERTER_DC_AC_EFFICIENCY,
    TRANSFORMER_INVERTER_DC_AC,
    INVERTER_DC_AC_COST_ANNUITY,
    TRANSFORMER_GENSET_,
    GENSET_COST_VAR,
    GENSET_EFFICIENCY,
    GENSET_MIN_LOADING,
    GENSET_MAX_LOADING,
    GENSET_COST_ANNUITY,
    TRANSFORMER_PCC_FEEDIN,
    PCOUPLING_COST_ANNUITY,
    PCOUPLING_COST_VAR,
    MAINGRID_FEEDIN_TARIFF,
    TRANSFORMER_PCC_CONSUMPTION,
    MAINGRID_ELECTRICITY_PRICE,
    PCOUPLING_EFFICIENCY,
    GENERIC_STORAGE,
    STORAGE_SOC_INITIAL,
    STORAGE_CAPACITY_COST_ANNUITY,
    STORAGE_COST_VAR,
    STORAGE_POWER_COST_ANNUITY,
    STORAGE_LOSS_TIMESTEP,
    STORAGE_SOC_MIN,
    STORAGE_SOC_MAX,
    STORAGE_EFFICIENCY_CHARGE,
    STORAGE_EFFICIENCY_DISCHARGE,
    STORAGE_CRATE_CHARGE,
    STORAGE_CRATE_DISCHARGE,
    SINK_EXCESS,
    TRANSFORMER_RECTIFIER,
    DISTRIBUTION_GRID_EFFICIENCY,
    SINK_DEMAND_AC,
    SINK_DEMAND_DC,
    SINK_MAINGRID_FEEDIN,
    GRID_AVAILABILITY,
    SINK_MAINGRID_FEEDIN_SYMBOLIC,
    PV_GENERATION,
    WIND_GENERATION,
    WIND_COST_ANNUITY,
    BUS_ELECTRICITY_NG_FEEDIN,
)

###############################################################################
# Define all oemof_functioncalls (including generate graph etc)
###############################################################################


######## Sources ########
def fuel(micro_grid_system, bus_fuel, experiment):
    logging.debug("Added to oemof model: source fuel")
    # Does NOT include a boundary for intendet minimal renewable factor (as in dispatch, operation costs in focus)
    source_fuel = solph.Source(
        label=SOURCE_FUEL,
        outputs={
            bus_fuel: solph.Flow(
                variable_costs=experiment[PRICE_FUEL]
                / experiment[COMBUSTION_VALUE_FUEL]
            )
        },
    )
    micro_grid_system.add(source_fuel)
    return


def shortage(
    micro_grid_system, bus_electricity_ac, bus_electricity_dc, experiment, case_dict
):
    """
    Creates source for shortages "source_shortage" including boundary conditions
    for maximal unserved demand and the variable costs of unserved demand.
    """
    logging.debug("Added to oemof model: source shortage")
    source_shortage = solph.Source(
        label=SOURCE_SHORTAGE,
        outputs={
            bus_electricity_ac: solph.Flow(
                variable_costs=experiment[SHORTAGE_PENALTY_COST],
                nominal_value=case_dict[MAX_SHORTAGE] * case_dict[TOTAL_DEMAND_AC],
                summed_max=1,
            ),
            bus_electricity_dc: solph.Flow(
                variable_costs=experiment["shortage_penalty_costs"],
                nominal_value=case_dict["max_shortage"] * case_dict["total_demand_dc"],
                summed_max=1,
            ),
        },
    )
    micro_grid_system.add(source_shortage)
    return source_shortage


def maingrid_consumption(micro_grid_system, experiment):
    logging.debug("Added to oemof model: maingrid consumption")
    # create and add demand sink to micro_grid_system - fixed
    bus_electricity_ng_consumption = solph.Bus(label=BUS_ELECTRICITY_NG_CONSUMPTION)
    micro_grid_system.add(bus_electricity_ng_consumption)

    source_maingrid_consumption = solph.Source(
        label=SOURCE_MAINGRID_CONSUMPTION,
        outputs={
            bus_electricity_ng_consumption: solph.Flow(
                fix=experiment[GRID_AVAILABILITY],
                investment=solph.Investment(ep_costs=0),
            )
        },
    )

    micro_grid_system.add(source_maingrid_consumption)

    sink_maingrid_consumption_symbolic = solph.Sink(
        label=SINK_MAINGRID_CONSUMPTION_SYMBOLIC,
        inputs={bus_electricity_ng_consumption: solph.Flow()},
    )
    micro_grid_system.add(sink_maingrid_consumption_symbolic)
    return bus_electricity_ng_consumption


######## Sources ########

######## Components ########
def pv_fix(micro_grid_system, bus_electricity_dc, experiment, capacity_pv):
    """
    Creates PV generation source "source_pv" with fix capacity,
    using the PV generation profile per kWp (scaled by capacity) with variable costs.
    """
    logging.debug("Added to oemof model: pv fix")
    source_pv = solph.Source(
        label=SOURCE_PV,
        outputs={
            bus_electricity_dc: solph.Flow(
                label=PV_GENERATION,
                fix=experiment[PV_GENERATION_PER_KWP],
                nominal_value=capacity_pv,
                variable_costs=experiment[PV_COST_VAR],
            )
        },
    )

    micro_grid_system.add(source_pv)
    return source_pv


def pv_oem(micro_grid_system, bus_electricity_dc, experiment):
    """
    Creates PV generation source "source_pv" for OEM,
    using the normed PV generation profile per kWp,
    investment costs and variable costs.
    """

    logging.debug("Added to oemof model: pv oem")
    peak_pv_generation = experiment[PEAK_PV_GENERATION_PER_KWP]
    pv_norm = experiment[PV_GENERATION_PER_KWP] / peak_pv_generation
    if pv_norm.any() > 1:
        logging.warning("Error, PV generation not normalized, greater than 1")
    if pv_norm.any() < 0:
        logging.warning("Error, PV generation negative")

    source_pv = solph.Source(
        label=SOURCE_PV,
        outputs={
            bus_electricity_dc: solph.Flow(
                label=PV_GENERATION,
                fix=pv_norm,
                investment=solph.Investment(
                    ep_costs=experiment[PV_COST_ANNUITY] / peak_pv_generation
                ),
                variable_costs=experiment[PV_COST_VAR] / peak_pv_generation,
            )
        },
    )
    micro_grid_system.add(source_pv)
    return source_pv


######## Components ########
def wind_fix(micro_grid_system, bus_electricity_ac, experiment, capacity_wind):
    logging.debug("Added to oemof model: wind")
    source_wind = solph.Source(
        label=SOURCE_WIND,
        outputs={
            bus_electricity_ac: solph.Flow(
                label=WIND_GENERATION,
                fix=experiment[WIND_GENERATION_PER_KW],
                nominal_value=capacity_wind,
                variable_costs=experiment[WIND_COST_VAR],
            )
        },
    )

    micro_grid_system.add(source_wind)
    return source_wind


def wind_oem(micro_grid_system, bus_electricity_ac, experiment):
    logging.debug("Added to oemof model: wind")
    peak_wind_generation = experiment[PEAK_WIND_GENERATION_PER_KW]
    wind_norm = experiment[WIND_GENERATION_PER_KW] / peak_wind_generation
    if wind_norm.any() > 1:
        logging.warning("Error, Wind generation not normalized, greater than 1")
    if wind_norm.any() < 0:
        logging.warning("Error, Wind generation negative")

    source_wind = solph.Source(
        label=SOURCE_WIND,
        outputs={
            bus_electricity_ac: solph.Flow(
                label=WIND_GENERATION,
                fix=wind_norm,
                investment=solph.Investment(
                    ep_costs=experiment[WIND_COST_ANNUITY] / peak_wind_generation
                ),
                variable_costs=experiment[WIND_COST_VAR] / peak_wind_generation,
            )
        },
    )
    micro_grid_system.add(source_wind)
    return source_wind


def rectifier_fix(
    micro_grid_system,
    bus_electricity_ac,
    bus_electricity_dc,
    experiment,
    capacity_rectifier,
):
    logging.debug("Added to oemof model: rectifier fix")
    rectifier = solph.Transformer(
        label=TRANSFORMER_RECTIFIER,
        inputs={
            bus_electricity_ac: solph.Flow(
                nominal_value=capacity_rectifier,
                variable_costs=experiment[RECTIFIER_AC_DC_COST_VAR],
            )
        },
        outputs={bus_electricity_dc: solph.Flow()},
        conversion_factors={bus_electricity_dc: experiment[RECTIFIER_AC_DC_EFFICIENCY]},
    )
    micro_grid_system.add(rectifier)
    return rectifier


def rectifier_oem(
    micro_grid_system, bus_electricity_ac, bus_electricity_dc, experiment
):
    logging.debug("Added to oemof model: rectifier oem")
    rectifier = solph.Transformer(
        label=TRANSFORMER_RECTIFIER,
        inputs={
            bus_electricity_ac: solph.Flow(
                investment=solph.Investment(
                    ep_costs=experiment[RECTIFIER_AC_DC_COST_ANNUITY]
                ),
                variable_costs=experiment[RECTIFIER_AC_DC_COST_VAR],
            )
        },
        outputs={bus_electricity_dc: solph.Flow()},
        conversion_factors={bus_electricity_dc: experiment[RECTIFIER_AC_DC_EFFICIENCY]},
    )
    micro_grid_system.add(rectifier)
    return rectifier


def inverter_dc_ac_fix(
    micro_grid_system,
    bus_electricity_ac,
    bus_electricity_dc,
    experiment,
    capacity_inverter_dc_ac,
):
    logging.debug("Added to oemof model: inverter_dc_ac fix")
    inverter_dc_ac = solph.Transformer(
        label=TRANSFORMER_INVERTER_DC_AC,
        inputs={
            bus_electricity_dc: solph.Flow(
                nominal_value=capacity_inverter_dc_ac,
                variable_costs=experiment[INVERTER_DC_AC_COST_VAR],
            )
        },
        outputs={bus_electricity_ac: solph.Flow()},
        conversion_factors={bus_electricity_ac: experiment[INVERTER_DC_AC_EFFICIENCY]},
    )
    micro_grid_system.add(inverter_dc_ac)
    return inverter_dc_ac


def inverter_dc_ac_oem(
    micro_grid_system, bus_electricity_ac, bus_electricity_dc, experiment
):
    logging.debug("Added to oemof model: inverter_dc_ac oem")
    inverter_dc_ac = solph.Transformer(
        label=TRANSFORMER_INVERTER_DC_AC,
        inputs={
            bus_electricity_dc: solph.Flow(
                investment=solph.Investment(
                    ep_costs=experiment[INVERTER_DC_AC_COST_ANNUITY]
                ),
                variable_costs=experiment[INVERTER_DC_AC_COST_VAR],
            )
        },
        outputs={bus_electricity_ac: solph.Flow()},
        conversion_factors={bus_electricity_ac: experiment[INVERTER_DC_AC_EFFICIENCY]},
    )
    micro_grid_system.add(inverter_dc_ac)
    return inverter_dc_ac


def genset_fix(
    micro_grid_system,
    bus_fuel,
    bus_electricity_ac,
    experiment,
    capacity_fuel_gen,
    number_of_equal_generators,
):
    logging.debug("Added to oemof model: genset fix no minload")
    dict_of_generators = {}
    for number in range(1, number_of_equal_generators + 1):
        genset = solph.Transformer(
            label=TRANSFORMER_GENSET_ + str(number),
            inputs={bus_fuel: solph.Flow()},
            outputs={
                bus_electricity_ac: solph.Flow(
                    nominal_value=capacity_fuel_gen / number_of_equal_generators,
                    variable_costs=experiment[GENSET_COST_VAR],
                )
            },
            conversion_factors={bus_electricity_ac: experiment[GENSET_EFFICIENCY]},
        )
        micro_grid_system.add(genset)
        dict_of_generators.update({number: genset})
    return dict_of_generators


def genset_fix_minload(
    micro_grid_system,
    bus_fuel,
    bus_electricity_ac,
    experiment,
    capacity_fuel_gen,
    number_of_equal_generators,
):
    """
    Generates fossil-fueled genset "transformer_fuel_generator" with nonconvex flow
    (min and max loading), generator efficiency, fixed capacity and variable costs.
    If minimal loading = 0, the generator is modeled without a nonconvex flow
    (which would result in an error due to constraint 'NonConvexFlow.min').
    """

    logging.debug("Added to oemof model: genset fix minload")
    dict_of_generators = {}
    for number in range(1, number_of_equal_generators + 1):
        genset = solph.Transformer(
            label=TRANSFORMER_GENSET_ + str(number),
            inputs={bus_fuel: solph.Flow()},
            outputs={
                bus_electricity_ac: solph.Flow(
                    nominal_value=capacity_fuel_gen / number_of_equal_generators,
                    variable_costs=experiment[GENSET_COST_VAR],
                    min=experiment[GENSET_MIN_LOADING],
                    max=experiment[GENSET_MAX_LOADING],
                    nonconvex=solph.NonConvex(),
                )
            },
            conversion_factors={bus_electricity_ac: experiment[GENSET_EFFICIENCY]},
        )
        micro_grid_system.add(genset)
        dict_of_generators.update({number: genset})

    return dict_of_generators


def genset_oem(
    micro_grid_system,
    bus_fuel,
    bus_electricity_ac,
    experiment,
    number_of_generators,
):
    """
    Generates fossi-fueled genset "transformer_fuel_generator" for OEM with generator efficiency,
    investment and variable costs.
    """
    logging.debug("Added to oemof model: genset oem no minload")
    dict_of_generators = {}
    for number in range(1, number_of_generators + 1):
        genset = solph.Transformer(
            label=TRANSFORMER_GENSET_ + str(number),
            inputs={bus_fuel: solph.Flow()},
            outputs={
                bus_electricity_ac: solph.Flow(
                    investment=solph.Investment(
                        ep_costs=experiment[GENSET_COST_ANNUITY]
                    ),
                    variable_costs=experiment[GENSET_COST_VAR],
                )
            },
            conversion_factors={bus_electricity_ac: experiment[GENSET_EFFICIENCY]},
        )
        micro_grid_system.add(genset)
        dict_of_generators.update({number: genset})
    return dict_of_generators


"""
def genset_oem_minload(micro_grid_system, bus_fuel, bus_electricity_ac, experiment):
    logging.debug('Added to oemof model: genset oem minload')
    logging.warning('Currently not possible to optimize capacities of generator with minimal loading with OEMOF!')
    genset = solph.Transformer(label="transformer_genset",
                                               inputs   ={bus_fuel: solph.Flow()},
                                               outputs  ={bus_electricity_ac: solph.Flow(
                                                   investment=solph.Investment(
                                                       ep_costs=experiment['genset_cost_annuity']),
                                                   variable_costs   = experiment['genset_cost_var'],
                                                   min=experiment['genset_min_loading'],
                                                   max=experiment['genset_max_loading'],
                                                   nonconvex=solph.NonConvex())},
                                               conversion_factors={ bus_electricity_ac: experiment['genset_efficiency']}
                                               )
    micro_grid_system.add(genset)
    return genset
    """


def pointofcoupling_feedin_fix(
    micro_grid_system,
    bus_electricity_ac,
    bus_electricity_ng_feedin,
    experiment,
    capacity_pointofcoupling,
):
    """
    Creates point of coupling "pointofcoupling_feedin" with fixed capacity,
    conversion factor and variable costs for the feed into the national grid.
    """
    logging.debug("Added to oemof model: pcc feedin fix")
    pointofcoupling_feedin = solph.Transformer(
        label=TRANSFORMER_PCC_FEEDIN,
        inputs={
            bus_electricity_ac: solph.Flow(
                nominal_value=capacity_pointofcoupling,
                variable_costs=experiment[PCOUPLING_COST_VAR]
                - experiment[MAINGRID_FEEDIN_TARIFF],
            )
        },
        outputs={bus_electricity_ng_feedin: solph.Flow()},
        conversion_factors={bus_electricity_ac: experiment[PCOUPLING_EFFICIENCY]},
    )  # is efficiency of the generator?? Then this should later on be included as a function of the load factor

    micro_grid_system.add(pointofcoupling_feedin)
    return


# point of coupling = max(demand) limits PV feed-in, therefore there should be a minimal pcc capacity defined with
# optimal larger size though OEM. existing = min_cap_pointofcoupling. but are all costs included?
def pointofcoupling_feedin_oem(
    micro_grid_system,
    bus_electricity_ac,
    bus_electricity_ng_feedin,
    experiment,
    min_cap_pointofcoupling,
):
    """
    Creates point of coupling "pointofcoupling_feedin" for OEM, conversion factor,
    investment and variable costs for the feed into the national grid.
    """
    logging.debug("Added to oemof model: pcc feedin oem")
    pointofcoupling_feedin = solph.Transformer(
        label=TRANSFORMER_PCC_FEEDIN,
        inputs={
            bus_electricity_ac: solph.Flow(
                investment=solph.Investment(
                    ep_costs=experiment[PCOUPLING_COST_ANNUITY]
                ),
                variable_costs=experiment[PCOUPLING_COST_VAR]
                - experiment[MAINGRID_FEEDIN_TARIFF],
            )
        },
        outputs={bus_electricity_ng_feedin: solph.Flow()},
        conversion_factors={bus_electricity_ac: experiment[PCOUPLING_EFFICIENCY]},
    )
    micro_grid_system.add(pointofcoupling_feedin)
    return


def pointofcoupling_consumption_fix(
    micro_grid_system,
    bus_electricity_ac,
    bus_electricity_ng_consumption,
    experiment,
    cap_pointofcoupling,
):
    logging.debug("Added to oemof model: pcc consumption fix")
    pointofcoupling_consumption = solph.Transformer(
        label=TRANSFORMER_PCC_CONSUMPTION,
        inputs={
            bus_electricity_ng_consumption: solph.Flow(
                nominal_value=cap_pointofcoupling,  # inflow is limited to nominal value!
                variable_costs=experiment[PCOUPLING_COST_VAR]
                + experiment[MAINGRID_ELECTRICITY_PRICE],
            )
        },
        outputs={bus_electricity_ac: solph.Flow()},
        conversion_factors={
            bus_electricity_ng_consumption: experiment[PCOUPLING_EFFICIENCY]
        },
    )  # is efficiency of the generator?? Then this should later on be included as a function of the load factor

    micro_grid_system.add(pointofcoupling_consumption)
    return pointofcoupling_consumption


def pointofcoupling_consumption_oem(
    micro_grid_system,
    bus_electricity_ac,
    bus_electricity_ng_consumption,
    experiment,
    min_cap_pointofcoupling,
):
    logging.debug("Added to oemof model: pcc consumption oem")
    pointofcoupling_consumption = solph.Transformer(
        label=TRANSFORMER_PCC_CONSUMPTION,
        inputs={
            bus_electricity_ng_consumption: solph.Flow(
                variable_costs=experiment[PCOUPLING_COST_VAR]
                + experiment[MAINGRID_ELECTRICITY_PRICE],
                investment=solph.Investment(
                    ep_costs=experiment[PCOUPLING_COST_ANNUITY]
                ),
            )
        },
        outputs={bus_electricity_ac: solph.Flow()},
        conversion_factors={
            bus_electricity_ng_consumption: experiment[PCOUPLING_EFFICIENCY]
        },
    )
    micro_grid_system.add(pointofcoupling_consumption)
    return pointofcoupling_consumption


def storage_fix(
    micro_grid_system,
    bus_electricity_dc,
    experiment,
    capacity_storage,
    power_storage,
):
    """
    Create storage unit "generic_storage" with fixed capacity,
    variable costs, maximal charge and discharge per timestep,
    capacity loss per timestep, charge and discharge efficiency,
    SOC boundaries (and initial SOC, possibly not needed).
    """
    logging.debug("Added to oemof model: storage fix")
    generic_storage = solph.components.GenericStorage(
        label=GENERIC_STORAGE,
        nominal_storage_capacity=capacity_storage,
        inputs={
            bus_electricity_dc: solph.Flow(
                nominal_value=capacity_storage * experiment[STORAGE_CRATE_CHARGE],
                variable_costs=experiment[STORAGE_COST_VAR],
            )
        },  # maximum charge possible in one timestep
        outputs={
            bus_electricity_dc: solph.Flow(
                nominal_value=power_storage  # capacity_storage*experiment['storage_Crate_discharge']
            )
        },  # maximum discharge possible in one timestep
        loss_rate=experiment[STORAGE_LOSS_TIMESTEP],  # from timestep to timestep
        min_storage_level=experiment[STORAGE_SOC_MIN],
        max_storage_level=experiment[STORAGE_SOC_MAX],
        initial_storage_level=experiment[STORAGE_SOC_INITIAL],  # in terms of SOC?
        inflow_conversion_factor=experiment[
            STORAGE_EFFICIENCY_CHARGE
        ],  # storing efficiency
        outflow_conversion_factor=experiment[STORAGE_EFFICIENCY_DISCHARGE],
    )  # efficiency of discharge
    micro_grid_system.add(generic_storage)
    return generic_storage


def storage_oem(micro_grid_system, bus_electricity_dc, experiment):
    """
    Create storage unit "generic_storage" for OEM with investment, variable costs,
    maximal charge and discharge per timestep,  capacity loss per timestep,
    charge and discharge efficiency,
    SOC boundaries (and initial SOC, possibly not needed).
    """
    logging.debug("Added to oemof model: storage oem")
    generic_storage = solph.components.GenericStorage(
        label=GENERIC_STORAGE,
        investment=solph.Investment(ep_costs=experiment[STORAGE_CAPACITY_COST_ANNUITY]),
        inputs={
            bus_electricity_dc: solph.Flow(variable_costs=experiment[STORAGE_COST_VAR])
        },
        outputs={
            bus_electricity_dc: solph.Flow(
                investment=solph.Investment(
                    ep_costs=experiment[STORAGE_POWER_COST_ANNUITY]
                )
            )
        },
        loss_rate=experiment[STORAGE_LOSS_TIMESTEP],  # from timestep to timestep
        min_storage_level=experiment[STORAGE_SOC_MIN],
        max_storage_level=experiment[STORAGE_SOC_MAX],
        inflow_conversion_factor=experiment[
            STORAGE_EFFICIENCY_CHARGE
        ],  # storing efficiency
        outflow_conversion_factor=experiment[
            STORAGE_EFFICIENCY_DISCHARGE
        ],  # efficiency of discharge
        invest_relation_input_capacity=experiment[
            STORAGE_CRATE_CHARGE
        ],  # storage can be charged with invest_relation_output_capacity*capacity in one timeperiod
        invest_relation_output_capacity=experiment[
            STORAGE_CRATE_DISCHARGE
        ],  # storage can be emptied with invest_relation_output_capacity*capacity in one timeperiod
    )
    micro_grid_system.add(generic_storage)
    return generic_storage


######## Components ########

######## Sinks ########
def excess(micro_grid_system, bus_electricity_ac, bus_electricity_dc):
    """
    Creates sink for excess electricity "sink_excess",
    eg. if PV panels generate too much electricity.
    """
    logging.debug("Added to oemof model: excess")
    # create and add excess electricity sink to micro_grid_system - variable
    sink_excess = solph.Sink(
        label=SINK_EXCESS,
        inputs={bus_electricity_ac: solph.Flow(), bus_electricity_dc: solph.Flow()},
    )
    micro_grid_system.add(sink_excess)
    return


def distribution_grid_ac(
    micro_grid_system,
    bus_electricity_ac,
    bus_electricity_demand,
    demand_profile,
    experiment,
):
    logging.debug("Added to oemof model: Distribution grid efficiency (AC)")
    distribution = solph.Transformer(
        label=TRANSFORMER_RECTIFIER,
        inputs={bus_electricity_ac: solph.Flow(investment=solph.Investment())},
        outputs={bus_electricity_demand: solph.Flow()},
        conversion_factors={
            bus_electricity_demand: experiment[DISTRIBUTION_GRID_EFFICIENCY]
        },
    )
    micro_grid_system.add(distribution)

    logging.debug("Added to oemof model: demand AC")
    # create and add demand sink to micro_grid_system - fixed
    sink_demand_ac = solph.Sink(
        label=SINK_DEMAND_AC,
        inputs={bus_electricity_ac: solph.Flow(fix=demand_profile, nominal_value=1)},
    )

    micro_grid_system.add(sink_demand_ac)

    return distribution


def demand_ac(micro_grid_system, bus_electricity_ac, demand_profile, demand_name):
    """
    Creates demand sink "sink_demand" with fixed flow
    """
    logging.debug("Added to oemof model: demand AC")
    # create and add demand sink to micro_grid_system - fixed
    sink_demand_ac = solph.Sink(
        label=SINK_DEMAND_AC,
        inputs={bus_electricity_ac: solph.Flow(fix=demand_profile, nominal_value=1)},
    )

    micro_grid_system.add(sink_demand_ac)
    demand_name.add(sink_demand_ac)
    return sink_demand_ac


def demand_dc(micro_grid_system, bus_electricity_dc, demand_profile, demand_name):
    """
    Creates demand sink "sink_demand" with fixed flow
    """
    logging.debug("Added to oemof model: demand DC")
    # create and add demand sink to micro_grid_system - fixed
    sink_demand_dc = solph.Sink(
        label="sink_demand_dc",
        inputs={bus_electricity_dc: solph.Flow(fix=demand_profile, nominal_value=1)},
    )
    micro_grid_system.add(sink_demand_dc)
    demand_name.add(sink_demand_dc)
    return sink_demand_dc


def maingrid_feedin(micro_grid_system, experiment):
    logging.debug("Added to oemof model: maingrid feedin")
    bus_electricity_ng_feedin = solph.Bus(label=BUS_ELECTRICITY_NG_FEEDIN)
    micro_grid_system.add(bus_electricity_ng_feedin)

    # create and add demand sink to micro_grid_system - fixed
    sink_maingrid_feedin = solph.Sink(
        label=SINK_MAINGRID_FEEDIN,
        inputs={
            bus_electricity_ng_feedin: solph.Flow(
                fix=experiment[GRID_AVAILABILITY],
                investment=solph.Investment(ep_costs=0),
            )
        },
    )
    micro_grid_system.add(sink_maingrid_feedin)

    # to fill in for not really provided feed in
    source_maingrid_feedin_symbolic = solph.Source(
        label=SINK_MAINGRID_FEEDIN_SYMBOLIC,
        outputs={bus_electricity_ng_feedin: solph.Flow()},
    )
    micro_grid_system.add(source_maingrid_feedin_symbolic)
    return bus_electricity_ng_feedin


######## Sinks ########
