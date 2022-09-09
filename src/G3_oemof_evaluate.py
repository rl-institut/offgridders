"""
Requires:
oemof, matplotlib, demandlib, pvlib
tables, tkinter
"""

import pandas as pd
import oemof.solph as solph

import logging

# Try to import matplotlib librar
import matplotlib.pyplot as plt

from src.constants import (
    EVALUATED_DAYS,
    DATE_TIME_INDEX,
    DEMAND,
    SEQUENCES,
    BUS_ELECTRICITY_AC,
    SINK_DEMAND_AC,
    SINK_DEMAND_AC_CRITICAL,
    FLOW,
    EVALUATION_PERSPECTIVE,
    INVERTER_DC_AC_EFFICIENCY,
    BUS_ELECTRICITY_DC,
    SINK_DEMAND_DC,
    SINK_DEMAND_DC_CRITICAL,
    RECTIFIER_AC_DC_EFFICIENCY,
    TOTAL_DEMAND_ANNUAL_KWH,
    DEMAND_PEAK_KW,
    ALLOW_SHORTAGE,
    SOURCE_SHORTAGE,
    TOTAL_DEMAND_SHORTAGE_AC_ANNUAL_KWH,
    DEMAND_SHORTAGE_AC,
    TOTAL_DEMAND_SHORTAGE_DC_ANNUAL_KWH,
    DEMAND_SHORTAGE_DC,
    TOTAL_DEMAND_SUPPLIED_ANNUAL_KWH,
    TOTAL_DEMAND_SHORTAGE_ANNUAL_KWH,
    DEMAND_SHORTAGE,
    DEMAND_SUPPLIED,
    SINK_EXCESS,
    TOTAL_DEMAND_EXCESS_AC_ANNUAL_KWH,
    EXCESS_GENERATION_AC,
    TOTAL_DEMAND_EXCESS_DC_ANNUAL_KWH,
    EXCESS_GENERATION_DC,
    TOTAL_DEMAND_EXCESS_ANNUAL_KWH,
    EXCESS_GENERATION,
    PV_FIXED_CAPACITY,
    SOURCE_PV,
    TOTAL_PV_GENERATION_KWH,
    PV_GENERATION_DC,
    PV_GENERATION_AC,
    PV_GENERATION,
    CAPACITY_PV_KWP,
    SCALARS,
    INVEST,
    RECTIFIER_AC_DC_FIXED_CAPACITY,
    TRANSFORMER_RECTIFIER,
    RECTIFIER_OUTPUT,
    RECTIFIER_INPUT,
    TOTAL_RECTIFIER_AC_DC_THROUGHPUT_KWH,
    CAPACITY_RECTIFIER_AC_DC_KW,
    INVERTER_DC_AC_FIXED_CAPACITY,
    TRANSFORMER_INVERTER_DC_AC,
    INVERTER_OUTPUT,
    INVERTER_INPUT,
    TOTAL_INVERTER_DC_AC_THROUGHPUT_KWH,
    CAPACITY_INVERTER_DC_AC_KW,
    WIND_FIXED_CAPACITY,
    SOURCE_WIND,
    TOTAL_WIND_GENERATION_KWH,
    WIND_GENERATION,
    CAPACITY_WIND_KW,
    GENSET_FIXED_CAPACITY,
    TRANSFORMER_GENSET_1,
    GENSET_1_GENERATION,
    NUMBER_OF_EQUAL_GENERATORS,
    TRANSFORMER_GENSET_,
    TOTAL_GENSET_GENERATION_KWH,
    GENSET_GENERATION,
    CAPACITY_GENSET_KW,
    BUS_FUEL,
    SOURCE_FUEL,
    CONSUMPTION_FUEL_ANNUAL_KWH,
    STORAGE_FIXED_CAPACITY,
    GENERIC_STORAGE,
    CAPACITY,
    TOTAL_STORAGE_THOUGHPUT_KWH,
    STORAGE_CHARGE_DC,
    STORAGE_DISCHARGE_DC,
    STORED_CAPACITY,
    STORAGE_CHARGE_AC,
    STORAGE_DISCHARGE_AC,
    STORAGE_CHARGE,
    STORAGE_DISCHARGE,
    CAPACITY_STORAGE_KWH,
    POWER_STORAGE_KW,
    STORAGE_FIXED_POWER,
    STORAGE_SOC,
    PCC_CONSUMPTION_FIXED_CAPACITY,
    PCC_FEEDIN_FIXED_CAPACITY,
    GRID_AVAILABILITY,
    TRANSFORMER_PCC_CONSUMPTION,
    CONSUMPTION_MAIN_GRID_MG_SIDE,
    CONSUMPTION_MAIN_GRID_MG_SIDE_ANNUAL_KWH,
    BUS_ELECTRICITY_NG_CONSUMPTION,
    CONSUMPTION_MAIN_GRID_UTILITY_SIDE_ANNUAL_KWH,
    AUTONOMY_FACTOR,
    TRANSFORMER_PCC_FEEDIN,
    FEEDIN_MAIN_GRID_MG_SIDE_ANNUAL_KWH,
    BUS_ELECTRICITY_NG_FEEDIN,
    FEEDIN_MAIN_GRID_UTILITY_SIDE_ANNUAL_KWH,
    CAPACITY_PCOUPLING_KW,
    TOTAL_PCOUPLING_THROUGHPUT_KWH,
    MAINGRID_RENEWABLE_SHARE,
    RES_SHARE,
    AC_SYSTEM,
    FEED_INTO_MAIN_GRID_MG_SIDE,
    DEMAND_AC,
    DEMAND_DC,
    DEMAND_AC_CRITICAL,
    DEMAND_DC_CRITICAL,
    GENSET_HOURS_OF_OPERATION,
    CRITICAL_CONSTRAINT,
    CRITICAL,
)


def join_e_flows_df(timeseries, name, e_flows_df):
    new_column = pd.DataFrame(timeseries.values, columns=[name], index=timeseries.index)
    e_flows_df = e_flows_df.join(new_column)
    return e_flows_df


def annual_value(name, timeseries, oemof_results, case_dict):
    value = sum(timeseries)
    value = value * 365 / case_dict[EVALUATED_DAYS]
    oemof_results.update({name: value})
    return


def get_demand(
    case_dict, oemof_results, electricity_bus_ac, electricity_bus_dc, experiment
):
    logging.debug("Evaluate flow: demand")
    # Get flow

    e_flows_df = pd.DataFrame(
        [0 for i in experiment[DATE_TIME_INDEX]],
        columns=[DEMAND],
        index=experiment[DATE_TIME_INDEX],
    )
    demand_ac = electricity_bus_ac[SEQUENCES][
        ((BUS_ELECTRICITY_AC, SINK_DEMAND_AC), FLOW)
    ]
    e_flows_df = join_e_flows_df(demand_ac, DEMAND_AC, e_flows_df)
    if case_dict[EVALUATION_PERSPECTIVE] == AC_SYSTEM:
        e_flows_df[DEMAND] += demand_ac
    else:
        e_flows_df[DEMAND] += demand_ac / experiment[INVERTER_DC_AC_EFFICIENCY]

    # if case_dict['pv_fixed_capacity'] != None \
    #        or case_dict['storage_fixed_capacity'] != None:

    demand_dc = electricity_bus_dc[SEQUENCES][
        ((BUS_ELECTRICITY_DC, SINK_DEMAND_DC), FLOW)
    ]
    e_flows_df = join_e_flows_df(demand_dc, DEMAND_DC, e_flows_df)
    if case_dict[EVALUATION_PERSPECTIVE] == AC_SYSTEM:
        e_flows_df[DEMAND] += demand_dc / experiment[RECTIFIER_AC_DC_EFFICIENCY]
    else:
        e_flows_df[DEMAND] += demand_dc

    critical_constraint = case_dict.get(CRITICAL_CONSTRAINT, False)
    if critical_constraint is True:
        # Add the critical demand to the total demand
        demand_ac_critical = electricity_bus_ac[SEQUENCES][
            ((BUS_ELECTRICITY_AC, SINK_DEMAND_AC_CRITICAL), FLOW)
        ]
        e_flows_df = join_e_flows_df(demand_ac_critical, DEMAND_AC_CRITICAL, e_flows_df)
        if case_dict[EVALUATION_PERSPECTIVE] == AC_SYSTEM:
            e_flows_df[DEMAND] += demand_ac_critical
        else:
            e_flows_df[DEMAND] += (
                demand_ac_critical / experiment[INVERTER_DC_AC_EFFICIENCY]
            )

        demand_dc_critical = electricity_bus_dc[SEQUENCES][
            ((BUS_ELECTRICITY_DC, SINK_DEMAND_DC), FLOW)
        ]
        e_flows_df = join_e_flows_df(demand_dc_critical, DEMAND_DC_CRITICAL, e_flows_df)
        if case_dict[EVALUATION_PERSPECTIVE] == AC_SYSTEM:
            e_flows_df[DEMAND] += (
                demand_dc_critical / experiment[RECTIFIER_AC_DC_EFFICIENCY]
            )
        else:
            e_flows_df[DEMAND] += demand_dc_critical

    annual_value(TOTAL_DEMAND_ANNUAL_KWH, e_flows_df[DEMAND], oemof_results, case_dict)

    oemof_results.update({DEMAND_PEAK_KW: max(e_flows_df[DEMAND])})
    return e_flows_df


def get_shortage(
    case_dict,
    oemof_results,
    electricity_bus_ac,
    electricity_bus_dc,
    experiment,
    e_flows_df,
):
    logging.debug("Evaluate flow: shortage")

    # Get flow
    shortage = pd.Series([0 for i in e_flows_df.index], index=e_flows_df.index)

    if case_dict[ALLOW_SHORTAGE] is True:
        if electricity_bus_ac != None:

            shortage_ac = electricity_bus_ac[SEQUENCES][
                ((SOURCE_SHORTAGE, BUS_ELECTRICITY_AC), FLOW)
            ]
            # aggregated flow into the AC bus
            annual_value(
                TOTAL_DEMAND_SHORTAGE_AC_ANNUAL_KWH,
                shortage_ac,
                oemof_results,
                case_dict,
            )
            e_flows_df = join_e_flows_df(shortage_ac, DEMAND_SHORTAGE_AC, e_flows_df)

            if case_dict[EVALUATION_PERSPECTIVE] == AC_SYSTEM:
                shortage += shortage_ac
            else:
                shortage += shortage_ac / experiment[INVERTER_DC_AC_EFFICIENCY]

        if electricity_bus_dc != None:

            shortage_dc = electricity_bus_dc[SEQUENCES][
                ((SOURCE_SHORTAGE, BUS_ELECTRICITY_DC), FLOW)
            ]
            # aggregated flow into the DC bus
            annual_value(
                TOTAL_DEMAND_SHORTAGE_DC_ANNUAL_KWH,
                shortage_dc,
                oemof_results,
                case_dict,
            )
            e_flows_df = join_e_flows_df(shortage_dc, DEMAND_SHORTAGE_DC, e_flows_df)

            if case_dict[EVALUATION_PERSPECTIVE] == AC_SYSTEM:
                shortage += shortage_dc / experiment[RECTIFIER_AC_DC_EFFICIENCY]
            else:
                shortage += shortage_dc

        # TODO make sure this does not raise errors when used without critical demand option
        if case_dict[EVALUATION_PERSPECTIVE] == AC_SYSTEM:
            demand_supplied = e_flows_df[DEMAND_AC_CRITICAL] + e_flows_df[DEMAND_AC] - shortage
        else:
            demand_supplied = e_flows_df[DEMAND_DC_CRITICAL] + e_flows_df[DEMAND_DC] - shortage

        annual_value(
            TOTAL_DEMAND_SUPPLIED_ANNUAL_KWH,
            demand_supplied,
            oemof_results,
            case_dict,
        )
        annual_value(
            TOTAL_DEMAND_SHORTAGE_ANNUAL_KWH, shortage, oemof_results, case_dict
        )
        e_flows_df = join_e_flows_df(shortage, DEMAND_SHORTAGE, e_flows_df)
        e_flows_df = join_e_flows_df(demand_supplied, DEMAND_SUPPLIED, e_flows_df)
    else:
        oemof_results.update(
            {TOTAL_DEMAND_SUPPLIED_ANNUAL_KWH: oemof_results[TOTAL_DEMAND_ANNUAL_KWH]}
        )
        oemof_results.update({TOTAL_DEMAND_SHORTAGE_ANNUAL_KWH: 0})
    return e_flows_df


def get_excess(
    case_dict, oemof_results, electricity_bus_ac, electricity_bus_dc, e_flows_df
):
    logging.debug("Evaluate excess: ")
    # Get flow
    excess = pd.Series([0 for i in e_flows_df.index], index=e_flows_df.index)

    if electricity_bus_ac != None:

        excess_ac = electricity_bus_ac[SEQUENCES][
            ((BUS_ELECTRICITY_AC, SINK_EXCESS), FLOW)
        ]
        excess += excess_ac
        annual_value(
            TOTAL_DEMAND_EXCESS_AC_ANNUAL_KWH, excess_ac, oemof_results, case_dict
        )
        e_flows_df = join_e_flows_df(excess_ac, EXCESS_GENERATION_AC, e_flows_df)

    if electricity_bus_dc != None:

        excess_dc = electricity_bus_dc[SEQUENCES][
            ((BUS_ELECTRICITY_DC, SINK_EXCESS), FLOW)
        ]
        excess += excess_dc
        annual_value(
            TOTAL_DEMAND_EXCESS_DC_ANNUAL_KWH, excess, oemof_results, case_dict
        )  # not given as result.csv right now
        e_flows_df = join_e_flows_df(excess_dc, EXCESS_GENERATION_DC, e_flows_df)

    annual_value(
        TOTAL_DEMAND_EXCESS_ANNUAL_KWH, excess, oemof_results, case_dict
    )  # not given as result.csv right now
    e_flows_df = join_e_flows_df(excess, EXCESS_GENERATION, e_flows_df)

    return e_flows_df


def get_pv(
    case_dict,
    oemof_results,
    electricity_bus_dc,
    experiment,
    e_flows_df,
    pv_generation_max,
):
    logging.debug("Evaluate flow: pv")
    # Get flow
    if case_dict[PV_FIXED_CAPACITY] != None:
        pv_gen = electricity_bus_dc[SEQUENCES][((SOURCE_PV, BUS_ELECTRICITY_DC), FLOW)]
        annual_value(TOTAL_PV_GENERATION_KWH, pv_gen, oemof_results, case_dict)
        e_flows_df = join_e_flows_df(pv_gen, PV_GENERATION_DC, e_flows_df)
        if case_dict[EVALUATION_PERSPECTIVE] == AC_SYSTEM:
            e_flows_df = join_e_flows_df(
                pv_gen / experiment[RECTIFIER_AC_DC_EFFICIENCY],
                PV_GENERATION_AC,
                e_flows_df,
            )

        if case_dict[EVALUATION_PERSPECTIVE] == AC_SYSTEM:
            e_flows_df = join_e_flows_df(
                e_flows_df[PV_GENERATION_AC], PV_GENERATION, e_flows_df
            )
        else:
            e_flows_df = join_e_flows_df(
                e_flows_df[PV_GENERATION_DC], PV_GENERATION, e_flows_df
            )
    else:
        oemof_results.update({TOTAL_PV_GENERATION_KWH: 0})

    # Get capacity
    if case_dict[PV_FIXED_CAPACITY] is False:
        if pv_generation_max > 1:
            oemof_results.update(
                {
                    CAPACITY_PV_KWP: electricity_bus_dc[SCALARS][
                        ((SOURCE_PV, BUS_ELECTRICITY_DC), INVEST)
                    ]
                    * pv_generation_max
                }
            )
        elif pv_generation_max > 0 and pv_generation_max < 1:
            oemof_results.update(
                {
                    CAPACITY_PV_KWP: electricity_bus_dc[SCALARS][
                        ((SOURCE_PV, BUS_ELECTRICITY_DC), INVEST)
                    ]
                    / pv_generation_max
                }
            )
        else:
            logging.warning("Error, Strange PV behaviour (PV gen < 0)")
    elif isinstance(case_dict[PV_FIXED_CAPACITY], float):
        oemof_results.update({CAPACITY_PV_KWP: case_dict[PV_FIXED_CAPACITY]})
    elif case_dict[PV_FIXED_CAPACITY] == None:
        oemof_results.update({CAPACITY_PV_KWP: 0})
    return e_flows_df


def get_rectifier(
    case_dict, oemof_results, electricity_bus_ac, electricity_bus_dc, e_flows_df
):
    logging.debug("Evaluate flow: rectifier")
    # Get flow
    if case_dict[RECTIFIER_AC_DC_FIXED_CAPACITY] != None:
        rectifier_out = electricity_bus_dc[SEQUENCES][
            ((TRANSFORMER_RECTIFIER, BUS_ELECTRICITY_DC), FLOW)
        ]
        e_flows_df = join_e_flows_df(rectifier_out, RECTIFIER_OUTPUT, e_flows_df)

        rectifier_in = electricity_bus_ac[SEQUENCES][
            ((BUS_ELECTRICITY_AC, TRANSFORMER_RECTIFIER), FLOW)
        ]
        e_flows_df = join_e_flows_df(rectifier_in, RECTIFIER_INPUT, e_flows_df)

        annual_value(
            TOTAL_RECTIFIER_AC_DC_THROUGHPUT_KWH,
            rectifier_in,
            oemof_results,
            case_dict,
        )
    else:
        oemof_results.update({TOTAL_RECTIFIER_AC_DC_THROUGHPUT_KWH: 0})

    # Get capacity
    if case_dict[RECTIFIER_AC_DC_FIXED_CAPACITY] is False:
        rectifier_capacity = electricity_bus_ac[SCALARS][
            ((BUS_ELECTRICITY_AC, TRANSFORMER_RECTIFIER), INVEST)
        ]
        oemof_results.update({CAPACITY_RECTIFIER_AC_DC_KW: rectifier_capacity})

    elif isinstance(case_dict[RECTIFIER_AC_DC_FIXED_CAPACITY], float):
        oemof_results.update(
            {CAPACITY_RECTIFIER_AC_DC_KW: case_dict[RECTIFIER_AC_DC_FIXED_CAPACITY]}
        )

    elif case_dict[RECTIFIER_AC_DC_FIXED_CAPACITY] == None:
        oemof_results.update({CAPACITY_RECTIFIER_AC_DC_KW: 0})
    return e_flows_df


def get_inverter(
    case_dict, oemof_results, electricity_bus_ac, electricity_bus_dc, e_flows_df
):
    logging.debug("Evaluate flow: rectifier")
    # Get flow
    if case_dict[INVERTER_DC_AC_FIXED_CAPACITY] != None:
        inverter_out = electricity_bus_ac[SEQUENCES][
            ((TRANSFORMER_INVERTER_DC_AC, BUS_ELECTRICITY_AC), FLOW)
        ]
        e_flows_df = join_e_flows_df(inverter_out, INVERTER_OUTPUT, e_flows_df)

        inverter_in = electricity_bus_dc[SEQUENCES][
            ((BUS_ELECTRICITY_DC, TRANSFORMER_INVERTER_DC_AC), FLOW)
        ]
        e_flows_df = join_e_flows_df(inverter_in, INVERTER_INPUT, e_flows_df)

        annual_value(
            TOTAL_INVERTER_DC_AC_THROUGHPUT_KWH,
            inverter_in,
            oemof_results,
            case_dict,
        )
    else:
        oemof_results.update({TOTAL_INVERTER_DC_AC_THROUGHPUT_KWH: 0})

    # Get capacity
    if case_dict[INVERTER_DC_AC_FIXED_CAPACITY] is False:
        inverter_capacity = electricity_bus_dc[SCALARS][
            ((BUS_ELECTRICITY_DC, TRANSFORMER_INVERTER_DC_AC), INVEST)
        ]
        oemof_results.update({CAPACITY_INVERTER_DC_AC_KW: inverter_capacity})

    elif isinstance(case_dict[INVERTER_DC_AC_FIXED_CAPACITY], float):
        oemof_results.update(
            {CAPACITY_INVERTER_DC_AC_KW: case_dict[INVERTER_DC_AC_FIXED_CAPACITY]}
        )

    elif case_dict[INVERTER_DC_AC_FIXED_CAPACITY] == None:
        oemof_results.update({CAPACITY_INVERTER_DC_AC_KW: 0})
    return e_flows_df


def get_wind(
    case_dict, oemof_results, electricity_bus_ac, e_flows_df, wind_generation_max
):
    logging.debug("Evaluate flow: wind")
    # Get flow
    if case_dict[WIND_FIXED_CAPACITY] != None:
        wind_gen = electricity_bus_ac[SEQUENCES][
            ((SOURCE_WIND, BUS_ELECTRICITY_AC), FLOW)
        ]
        annual_value(TOTAL_WIND_GENERATION_KWH, wind_gen, oemof_results, case_dict)
        e_flows_df = join_e_flows_df(wind_gen, WIND_GENERATION, e_flows_df)
    else:
        oemof_results.update({TOTAL_WIND_GENERATION_KWH: 0})

    # Get capacity
    if case_dict[WIND_FIXED_CAPACITY] is False:
        if wind_generation_max > 1:
            oemof_results.update(
                {
                    CAPACITY_WIND_KW: electricity_bus_ac[SCALARS][
                        ((SOURCE_WIND, BUS_ELECTRICITY_AC), INVEST)
                    ]
                    * wind_generation_max
                }
            )
        elif wind_generation_max > 0 and wind_generation_max < 1:
            oemof_results.update(
                {
                    CAPACITY_WIND_KW: electricity_bus_ac[SCALARS][
                        ((SOURCE_WIND, BUS_ELECTRICITY_AC), INVEST)
                    ]
                    / wind_generation_max
                }
            )
        else:
            logging.warning("Error, Strange Wind behaviour (Wind gen < 0)")
    elif isinstance(case_dict[WIND_FIXED_CAPACITY], float):
        oemof_results.update({CAPACITY_WIND_KW: case_dict[WIND_FIXED_CAPACITY]})
    elif case_dict[WIND_FIXED_CAPACITY] == None:
        oemof_results.update({CAPACITY_WIND_KW: 0})
    return e_flows_df


def get_genset(case_dict, oemof_results, electricity_bus_ac, e_flows_df):
    logging.debug("Evaluate flow: genset")
    # Get flow
    if case_dict[GENSET_FIXED_CAPACITY] != None:
        genset = electricity_bus_ac[SEQUENCES][
            ((TRANSFORMER_GENSET_1, BUS_ELECTRICITY_AC), FLOW)
        ]
        e_flows_df = join_e_flows_df(genset, GENSET_1_GENERATION, e_flows_df)
        total_genset = genset
        for number in range(2, case_dict[NUMBER_OF_EQUAL_GENERATORS] + 1):
            genset = electricity_bus_ac[SEQUENCES][
                (
                    (TRANSFORMER_GENSET_ + str(number), BUS_ELECTRICITY_AC),
                    FLOW,
                )
            ]
            e_flows_df = join_e_flows_df(
                genset, "Genset " + str(number) + " generation", e_flows_df
            )
            total_genset += genset
        annual_value(
            TOTAL_GENSET_GENERATION_KWH, total_genset, oemof_results, case_dict
        )
        e_flows_df = join_e_flows_df(total_genset, GENSET_GENERATION, e_flows_df)
    else:
        oemof_results.update({TOTAL_GENSET_GENERATION_KWH: 0})

    # Get capacity
    if case_dict[GENSET_FIXED_CAPACITY] is False:
        # Optimized generator capacity (sum)
        genset_capacity = 0
        for number in range(1, case_dict[NUMBER_OF_EQUAL_GENERATORS] + 1):
            genset_capacity += electricity_bus_ac[SCALARS][
                (
                    (TRANSFORMER_GENSET_ + str(number), BUS_ELECTRICITY_AC),
                    INVEST,
                )
            ]
        oemof_results.update({CAPACITY_GENSET_KW: genset_capacity})
    elif isinstance(case_dict[GENSET_FIXED_CAPACITY], float):
        oemof_results.update({CAPACITY_GENSET_KW: case_dict[GENSET_FIXED_CAPACITY]})
    elif case_dict[GENSET_FIXED_CAPACITY] == None:
        oemof_results.update({CAPACITY_GENSET_KW: 0})

    # Get hours of operation:
    if case_dict[GENSET_FIXED_CAPACITY] != None:
        get_hours_of_operation(oemof_results, case_dict, e_flows_df[GENSET_GENERATION])
    else:
        oemof_results.update({GENSET_HOURS_OF_OPERATION: 0})
    return e_flows_df


def get_hours_of_operation(oemof_results, case_dict, genset_generation_total):
    """
    Calculates the total hours of genset generation (aggregated generation) of the evaluated timeframe.

    Parameters
    ----------
    oemof_results: dict
        Dict of all results of the simulation

    genset_generation_total: pd.Series
        Dispatch of the gensets, aggregated

    Returns
    -------
    Updates oemof_results with annual value of the GENSET_HOURS_OF_OPERATION.
    """
    operation_boolean = genset_generation_total.where(
        genset_generation_total == 0, other=1
    )
    annual_value(GENSET_HOURS_OF_OPERATION, operation_boolean, oemof_results, case_dict)
    return operation_boolean


def get_fuel(case_dict, oemof_results, results):
    logging.debug("Evaluate flow: fuel")
    if case_dict[GENSET_FIXED_CAPACITY] != None:
        fuel_bus = solph.views.node(results, BUS_FUEL)
        fuel = fuel_bus[SEQUENCES][((SOURCE_FUEL, BUS_FUEL), FLOW)]
        annual_value(CONSUMPTION_FUEL_ANNUAL_KWH, fuel, oemof_results, case_dict)
    else:
        oemof_results.update({CONSUMPTION_FUEL_ANNUAL_KWH: 0})
    return


def get_storage(case_dict, oemof_results, experiment, results, e_flows_df):
    logging.debug("Evaluate flow: storage")
    # Get flow
    if case_dict[STORAGE_FIXED_CAPACITY] != None:
        storage = solph.views.node(results, GENERIC_STORAGE)
        storage_discharge = storage[SEQUENCES][
            ((GENERIC_STORAGE, BUS_ELECTRICITY_DC), FLOW)
        ]

        storage_charge = storage[SEQUENCES][
            ((BUS_ELECTRICITY_DC, GENERIC_STORAGE), FLOW)
        ]
        stored_capacity = storage[SEQUENCES][
            ((GENERIC_STORAGE, "None"), "storage_content")
        ]
        annual_value(
            TOTAL_STORAGE_THOUGHPUT_KWH, storage_charge, oemof_results, case_dict
        )

        e_flows_df = join_e_flows_df(storage_charge, STORAGE_CHARGE_DC, e_flows_df)
        e_flows_df = join_e_flows_df(
            storage_discharge, STORAGE_DISCHARGE_DC, e_flows_df
        )
        e_flows_df = join_e_flows_df(stored_capacity, STORED_CAPACITY, e_flows_df)

        if case_dict[EVALUATION_PERSPECTIVE] == AC_SYSTEM:
            e_flows_df = join_e_flows_df(
                storage_charge / experiment[RECTIFIER_AC_DC_EFFICIENCY],
                STORAGE_CHARGE_AC,
                e_flows_df,
            )
            e_flows_df = join_e_flows_df(
                storage_discharge / experiment[INVERTER_DC_AC_EFFICIENCY],
                STORAGE_DISCHARGE_AC,
                e_flows_df,
            )
            e_flows_df = join_e_flows_df(
                e_flows_df[STORAGE_CHARGE_AC], STORAGE_CHARGE, e_flows_df
            )
            e_flows_df = join_e_flows_df(
                e_flows_df[STORAGE_DISCHARGE_AC], STORAGE_DISCHARGE, e_flows_df
            )
        else:
            e_flows_df = join_e_flows_df(
                e_flows_df[STORAGE_CHARGE_DC], STORAGE_CHARGE, e_flows_df
            )
            e_flows_df = join_e_flows_df(
                e_flows_df[STORAGE_DISCHARGE_DC], STORAGE_DISCHARGE, e_flows_df
            )
    else:
        oemof_results.update({TOTAL_STORAGE_THOUGHPUT_KWH: 0})

    # Get capacity
    if case_dict[STORAGE_FIXED_CAPACITY] is False:
        # Optimized storage capacity
        storage = solph.views.node(results, GENERIC_STORAGE)
        storage_capacity = storage[SCALARS][((GENERIC_STORAGE, "None"), INVEST)]

        electricity_bus_dc = solph.views.node(results, BUS_ELECTRICITY_DC)
        storage_power = electricity_bus_dc[SCALARS][
            ((GENERIC_STORAGE, BUS_ELECTRICITY_DC), INVEST)
        ]

        oemof_results.update(
            {
                CAPACITY_STORAGE_KWH: storage_capacity,
                POWER_STORAGE_KW: storage_power,
            }
        )

    elif isinstance(case_dict[STORAGE_FIXED_CAPACITY], float):
        oemof_results.update(
            {
                CAPACITY_STORAGE_KWH: case_dict[STORAGE_FIXED_CAPACITY],
                POWER_STORAGE_KW: case_dict[STORAGE_FIXED_POWER],
            }
        )

    elif case_dict[STORAGE_FIXED_CAPACITY] == None:
        oemof_results.update({CAPACITY_STORAGE_KWH: 0, POWER_STORAGE_KW: 0})

    # calculate SOC of battery:
    if oemof_results[CAPACITY_STORAGE_KWH] > 0:
        e_flows_df = join_e_flows_df(
            stored_capacity / oemof_results[CAPACITY_STORAGE_KWH],
            STORAGE_SOC,
            e_flows_df,
        )
    else:
        e_flows_df = join_e_flows_df(
            pd.Series([0 for t in e_flows_df.index], index=e_flows_df.index),
            STORAGE_SOC,
            e_flows_df,
        )

    return e_flows_df


def get_national_grid(case_dict, oemof_results, results, e_flows_df, grid_availability):
    logging.debug("Evaluate flow: main grid")
    micro_grid_bus = solph.views.node(results, BUS_ELECTRICITY_AC)
    # define grid availability
    if (
        case_dict[PCC_CONSUMPTION_FIXED_CAPACITY] != None
        or case_dict[PCC_FEEDIN_FIXED_CAPACITY] != None
    ):
        e_flows_df = join_e_flows_df(grid_availability, GRID_AVAILABILITY, e_flows_df)
    else:
        grid_availability_symbolic = pd.Series(
            [0 for i in e_flows_df.index], index=e_flows_df.index
        )
        e_flows_df = join_e_flows_df(
            grid_availability_symbolic, GRID_AVAILABILITY, e_flows_df
        )

    if case_dict[PCC_CONSUMPTION_FIXED_CAPACITY] != None:
        consumption_mg_side = micro_grid_bus[SEQUENCES][
            ((TRANSFORMER_PCC_CONSUMPTION, BUS_ELECTRICITY_AC), FLOW)
        ]
        e_flows_df = join_e_flows_df(
            consumption_mg_side, CONSUMPTION_MAIN_GRID_MG_SIDE, e_flows_df
        )
        annual_value(
            CONSUMPTION_MAIN_GRID_MG_SIDE_ANNUAL_KWH,
            consumption_mg_side,
            oemof_results,
            case_dict,
        )
        bus_electricity_ng_consumption = solph.views.node(
            results, BUS_ELECTRICITY_NG_CONSUMPTION
        )
        consumption_utility_side = bus_electricity_ng_consumption[SEQUENCES][
            (
                (BUS_ELECTRICITY_NG_CONSUMPTION, TRANSFORMER_PCC_CONSUMPTION),
                FLOW,
            )
        ]
        e_flows_df = join_e_flows_df(
            consumption_utility_side,
            "Consumption from main grid (utility side)",
            e_flows_df,
        )
        annual_value(
            CONSUMPTION_MAIN_GRID_UTILITY_SIDE_ANNUAL_KWH,
            consumption_utility_side,
            oemof_results,
            case_dict,
        )

    else:
        oemof_results.update(
            {
                CONSUMPTION_MAIN_GRID_MG_SIDE_ANNUAL_KWH: 0,
                CONSUMPTION_MAIN_GRID_UTILITY_SIDE_ANNUAL_KWH: 0,
            }
        )

    if oemof_results[TOTAL_DEMAND_SUPPLIED_ANNUAL_KWH] > 0:
        oemof_results.update(
            {
                AUTONOMY_FACTOR: (
                    oemof_results[TOTAL_DEMAND_SUPPLIED_ANNUAL_KWH]
                    - oemof_results[CONSUMPTION_MAIN_GRID_MG_SIDE_ANNUAL_KWH]
                )
                / oemof_results[TOTAL_DEMAND_SUPPLIED_ANNUAL_KWH]
            }
        )
    else:
        oemof_results.update({AUTONOMY_FACTOR: 0})

    if case_dict[PCC_FEEDIN_FIXED_CAPACITY] != None:
        feedin_mg_side = micro_grid_bus[SEQUENCES][
            ((BUS_ELECTRICITY_AC, TRANSFORMER_PCC_FEEDIN), FLOW)
        ]
        e_flows_df = join_e_flows_df(
            feedin_mg_side, FEED_INTO_MAIN_GRID_MG_SIDE, e_flows_df
        )
        annual_value(
            FEEDIN_MAIN_GRID_MG_SIDE_ANNUAL_KWH,
            feedin_mg_side,
            oemof_results,
            case_dict,
        )

        bus_electricity_ng_feedin = solph.views.node(results, BUS_ELECTRICITY_NG_FEEDIN)
        feedin_utility_side = bus_electricity_ng_feedin[SEQUENCES][
            ((TRANSFORMER_PCC_FEEDIN, BUS_ELECTRICITY_NG_FEEDIN), FLOW)
        ]
        e_flows_df = join_e_flows_df(
            feedin_utility_side, "Feed into main grid (utility side)", e_flows_df
        )
        annual_value(
            FEEDIN_MAIN_GRID_UTILITY_SIDE_ANNUAL_KWH,
            feedin_utility_side,
            oemof_results,
            case_dict,
        )
    else:
        oemof_results.update(
            {
                FEEDIN_MAIN_GRID_MG_SIDE_ANNUAL_KWH: 0,
                FEEDIN_MAIN_GRID_UTILITY_SIDE_ANNUAL_KWH: 0,
            }
        )

    # get capacities
    if (
        case_dict[PCC_CONSUMPTION_FIXED_CAPACITY] != None
        or case_dict[PCC_FEEDIN_FIXED_CAPACITY] != None
    ):
        pcc_cap = []
        if case_dict[PCC_CONSUMPTION_FIXED_CAPACITY] is False:
            pcc_cap.append(consumption_utility_side.max())
        elif isinstance(case_dict[PCC_CONSUMPTION_FIXED_CAPACITY], float):
            pcc_cap.append(case_dict[PCC_CONSUMPTION_FIXED_CAPACITY])

        if case_dict[PCC_FEEDIN_FIXED_CAPACITY] is False:
            pcc_cap.append(feedin_utility_side.max())
        elif isinstance(case_dict[PCC_FEEDIN_FIXED_CAPACITY], float):
            pcc_cap.append(case_dict[PCC_FEEDIN_FIXED_CAPACITY])

        oemof_results.update({CAPACITY_PCOUPLING_KW: max(pcc_cap)})
    elif (
        case_dict[PCC_CONSUMPTION_FIXED_CAPACITY] == None
        and case_dict[PCC_FEEDIN_FIXED_CAPACITY] == None
    ):
        oemof_results.update({CAPACITY_PCOUPLING_KW: 0})
    else:
        logging.warning(
            "Invalid value of pcc_consumption_fixed_capacity and/or pcc_feedin_fixed_capacity."
        )

    total_pcoupling_throughput_kWh = 0
    if (
        case_dict[PCC_CONSUMPTION_FIXED_CAPACITY] != None
        or case_dict[PCC_FEEDIN_FIXED_CAPACITY] != None
    ):
        if case_dict[PCC_CONSUMPTION_FIXED_CAPACITY] != None:
            total_pcoupling_throughput_kWh += oemof_results[
                CONSUMPTION_MAIN_GRID_MG_SIDE_ANNUAL_KWH
            ]  # payments also for inverter loss
        if case_dict[PCC_FEEDIN_FIXED_CAPACITY] != None:
            total_pcoupling_throughput_kWh += oemof_results[
                FEEDIN_MAIN_GRID_MG_SIDE_ANNUAL_KWH
            ]

    oemof_results.update(
        {TOTAL_PCOUPLING_THROUGHPUT_KWH: total_pcoupling_throughput_kWh}
    )

    return e_flows_df


def get_res_share(case_dict, oemof_results, experiment):
    logging.debug("Evaluate: res share")
    total_generation = oemof_results[TOTAL_GENSET_GENERATION_KWH]
    total_generation += oemof_results[CONSUMPTION_MAIN_GRID_MG_SIDE_ANNUAL_KWH]
    total_generation += oemof_results[TOTAL_PV_GENERATION_KWH]
    total_generation += oemof_results[TOTAL_WIND_GENERATION_KWH]

    total_fossil_generation = oemof_results[TOTAL_GENSET_GENERATION_KWH]
    # attention: only effectively used electricity consumption counts for renewable share
    total_fossil_generation += oemof_results[
        CONSUMPTION_MAIN_GRID_MG_SIDE_ANNUAL_KWH
    ] * (1 - experiment[MAINGRID_RENEWABLE_SHARE])
    if total_generation > 0:
        res_share = abs(1 - total_fossil_generation / total_generation)
    else:
        res_share = 0
        logging.warning(
            "Total generation is zero. Please check energy system - is the grid available in evaluated timeframe?"
        )

    oemof_results.update({RES_SHARE: res_share})
    return
