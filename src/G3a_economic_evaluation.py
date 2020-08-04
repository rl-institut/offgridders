###############################################################################
# Imports and initialize
###############################################################################

import logging

# Try to import matplotlib librar
from src.constants import (
    PCC_CONSUMPTION_FIXED_CAPACITY,
    PCC_FEEDIN_FIXED_CAPACITY,
    NPV,
    ANNUITY,
    ANNUITY_FACTOR,
    TOTAL_DEMAND_SUPPLIED_ANNUAL_KWH,
    LCOE,
    EVALUATED_DAYS,
    PV_COST_ANNUITY,
    ANNUITY_PV,
    CAPACITY_PV_KWP,
    ANNUITY_WIND,
    WIND_COST_ANNUITY,
    CAPACITY_WIND_KW,
    ANNUITY_STORAGE,
    STORAGE_CAPACITY_COST_ANNUITY,
    CAPACITY_STORAGE_KWH,
    STORAGE_POWER_COST_ANNUITY,
    POWER_STORAGE_KW,
    ANNUITY_GENSET,
    GENSET_COST_ANNUITY,
    CAPACITY_GENSET_KW,
    ANNUITY_RECTIFIER_AC_DC,
    RECTIFIER_AC_DC_COST_ANNUITY,
    CAPACITY_RECTIFIER_AC_DC_KW,
    ANNUITY_INVERTER_DC_AC,
    INVERTER_DC_AC_COST_ANNUITY,
    CAPACITY_INVERTER_DC_AC_KW,
    PROJECT,
    DISTRIBUTION_GRID,
    ANNUITY_PCOUPLING,
    PCOUPLING_COST_ANNUITY,
    CAPACITY_PCOUPLING_KW,
    ANNUITY_MAINGRID_EXTENSION,
    MAINGRID_EXTENSION_COST_ANNUITY,
    MAINGRID_DISTANCE,
    PV,
    WIND,
    GENSET,
    STORAGE,
    PCOUPLING,
    MAINGRID_EXTENSION,
    RECTIFIER_AC_DC,
    INVERTER_DC_AC,
    PV_COST_INVESTMENT,
    SHORTAGE_CAPACITY_COST_INVESTMENT,
    STORAGE_POWER_COST_INVESTMENT,
    MAINGRID_EXTENSION_COST_INVESTMENT,
    FIRST_INVESTMENT,
    SHORTAGE_CAPACITY_COST_OPEX,
    STORAGE_CAPACITY_LIFETIME,
    STORAGE_POWER_COST_OPEX,
    STORAGE_POWER_LIFETIME,
    OPERATION_MAINTAINANCE_EXPENDITURES,
    CONSUMPTION_FUEL_ANNUAL_L,
    CONSUMPTION_FUEL_ANNUAL_KWH,
    COMBUSTION_VALUE_FUEL,
    EXPENDITURES_FUEL_ANNUAL,
    PRICE_FUEL,
    EXPENDITURES_FUEL_TOTAL,
    EXPENDITURES_MAIN_GRID_CONSUMPTION_ANNUAL,
    CONSUMPTION_MAIN_GRID_MG_SIDE_ANNUAL_KWH,
    MAINGRID_ELECTRICITY_PRICE,
    EXPENDITURES_MAIN_GRID_CONSUMPTION_TOTAL,
    EXPENDITURES_SHORTAGE_ANNUAL,
    TOTAL_DEMAND_SHORTAGE_ANNUAL_KWH,
    SHORTAGE_PENALTY_COST,
    EXPENDITURES_SHORTAGE_TOTAL,
    COMMENTS,
    REVENUE_MAIN_GRID_FEEDIN_ANNUAL,
    FEEDIN_MAIN_GRID_MG_SIDE_ANNUAL_KWH,
    MAINGRID_FEEDIN_TARIFF,
    REVENUE_MAIN_GRID_FEEDIN_TOTAL,
    CO2_EMISSIONS_KGC02EQ, SUFFIX_COST_INVESTMENT, SUFFIX_LIFETIME, SUFFIX_COST_OPEX, SUFFIX_COST_VAR, SUFFIX_KW,
    SUFFIX_GENERATION_KWH, SUFFIX_THROUGHPUT_KWH, SUFFIX_COST_ANNUITY, PREFIX_ANNUITY, PREFIX_CAPACITY, PREFIX_OM_VAR,
    PREFIX_TOTAL, PREFIX_COSTS, FUEL_CO2_EMISSION_FACTOR)

try:
    import matplotlib.pyplot as plt
except ImportError:
    logging.warning("Attention! matplotlib could not be imported.")
    plt = None

###############################################################################
#
###############################################################################


def project_annuities(case_dict, oemof_results, experiment):
    # Define all annuities based on component capacities (Capex+Opex), add var. operational costs
    # Extrapolate to costs of whole year
    annuities_365(case_dict, oemof_results, experiment)

    # Add costs related to annuities
    costs(oemof_results, experiment)

    # Expenditures for fuel
    expenditures_fuel(oemof_results, experiment)

    # Expenditures for shortage
    expenditures_shortage(oemof_results, experiment)

    if case_dict[PCC_CONSUMPTION_FIXED_CAPACITY] != None:
        # ---------Expenditures from electricity consumption from main grid ----------#
        expenditures_main_grid_consumption(oemof_results, experiment)

    if case_dict[PCC_FEEDIN_FIXED_CAPACITY] != None:
        # ---------Revenues from electricity feed-in to main grid ----------#
        revenue_main_grid_feedin(oemof_results, experiment)

    oemof_results.update({NPV: oemof_results[ANNUITY] * experiment[ANNUITY_FACTOR]})

    if oemof_results[TOTAL_DEMAND_SUPPLIED_ANNUAL_KWH] > 0:
        oemof_results.update(
            {
                LCOE: oemof_results[ANNUITY]
                / oemof_results[TOTAL_DEMAND_SUPPLIED_ANNUAL_KWH]
            }
        )
    else:
        oemof_results.update({LCOE: 0})
    return


def annuities_365(case_dict, oemof_results, experiment):
    evaluated_days = case_dict[EVALUATED_DAYS]

    logging.debug(
        "Economic evaluation. Calculating investment costs over analysed timeframe."
    )

    interval_annuity = {
        ANNUITY_PV: experiment[PV_COST_ANNUITY] * oemof_results[CAPACITY_PV_KWP],
        ANNUITY_WIND: experiment[WIND_COST_ANNUITY] * oemof_results[CAPACITY_WIND_KW],
        ANNUITY_STORAGE: experiment[STORAGE_CAPACITY_COST_ANNUITY]
        * oemof_results[CAPACITY_STORAGE_KWH]
        + experiment[STORAGE_POWER_COST_ANNUITY] * oemof_results[POWER_STORAGE_KW],
        ANNUITY_GENSET: experiment[GENSET_COST_ANNUITY]
        * oemof_results[CAPACITY_GENSET_KW],
        ANNUITY_RECTIFIER_AC_DC: experiment[RECTIFIER_AC_DC_COST_ANNUITY]
        * oemof_results[CAPACITY_RECTIFIER_AC_DC_KW],
        ANNUITY_INVERTER_DC_AC: experiment[INVERTER_DC_AC_COST_ANNUITY]
        * oemof_results[CAPACITY_INVERTER_DC_AC_KW],
    }

    list_fix = [PROJECT, DISTRIBUTION_GRID]
    for item in list_fix:
        interval_annuity.update({PREFIX_ANNUITY + item: experiment[item + SUFFIX_COST_ANNUITY]})

    if (
        case_dict[PCC_CONSUMPTION_FIXED_CAPACITY] != None
        and case_dict[PCC_FEEDIN_FIXED_CAPACITY] != None
    ):
        interval_annuity.update(
            {
                ANNUITY_PCOUPLING: 2
                * experiment[PCOUPLING_COST_ANNUITY]
                * oemof_results[CAPACITY_PCOUPLING_KW]
            }
        )
    else:
        interval_annuity.update(
            {
                ANNUITY_PCOUPLING: experiment[PCOUPLING_COST_ANNUITY]
                * oemof_results[CAPACITY_PCOUPLING_KW]
            }
        )

    # Main grid extension
    if (
        case_dict[PCC_CONSUMPTION_FIXED_CAPACITY] != None
        or case_dict[PCC_FEEDIN_FIXED_CAPACITY] != None
    ):
        interval_annuity.update(
            {
                ANNUITY_MAINGRID_EXTENSION: experiment[MAINGRID_EXTENSION_COST_ANNUITY]
                * experiment[MAINGRID_DISTANCE]
            }
        )
    else:
        interval_annuity.update({ANNUITY_MAINGRID_EXTENSION: 0})

    component_list = [
        PV,
        WIND,
        GENSET,
        STORAGE,
        PCOUPLING,
        MAINGRID_EXTENSION,
        DISTRIBUTION_GRID,
        RECTIFIER_AC_DC,
        INVERTER_DC_AC,
        PROJECT,
    ]

    # include in oemof_results just first investment costs
    investment = 0
    for item in component_list:
        if item == PV:
            investment += (
                experiment[PV_COST_INVESTMENT] * oemof_results[CAPACITY_PV_KWP]
            )
        elif item == STORAGE:
            investment += (
                experiment[SHORTAGE_CAPACITY_COST_INVESTMENT]
                * oemof_results[CAPACITY_STORAGE_KWH]
            )
            investment += (
                experiment[STORAGE_POWER_COST_INVESTMENT]
                * oemof_results[CAPACITY_STORAGE_KWH]
            )
        elif item == MAINGRID_EXTENSION:
            investment += (
                experiment[MAINGRID_EXTENSION_COST_INVESTMENT]
                * experiment[MAINGRID_DISTANCE]
            )
        elif item in [DISTRIBUTION_GRID, PROJECT]:
            investment += experiment[item + SUFFIX_COST_INVESTMENT]
        else:
            investment += (
                experiment[item + SUFFIX_COST_INVESTMENT]
                * oemof_results[PREFIX_CAPACITY + item + SUFFIX_KW]
            )

    oemof_results.update({FIRST_INVESTMENT: investment})

    logging.debug("Economic evaluation. Calculating O&M costs over analysed timeframe.")

    om_var_interval = {}
    om = 0  # first, var costs are included, then opex costs and finally expenditures
    for item in [PV, WIND, GENSET]:
        om_var_interval.update(
            {
                PREFIX_OM_VAR
                + item: oemof_results[PREFIX_TOTAL + item + SUFFIX_GENERATION_KWH]
                * experiment[item + SUFFIX_COST_VAR]
            }
        )
        om += (
            oemof_results[PREFIX_TOTAL + item + SUFFIX_GENERATION_KWH]
            * experiment[item + SUFFIX_COST_VAR]
        )

    for item in [PCOUPLING, STORAGE, RECTIFIER_AC_DC, INVERTER_DC_AC]:
        om_var_interval.update(
            {
                PREFIX_OM_VAR
                + item: oemof_results[PREFIX_TOTAL + item + SUFFIX_THROUGHPUT_KWH]
                * experiment[item + SUFFIX_COST_VAR]
            }
        )
        om += (
            oemof_results[PREFIX_TOTAL + item + SUFFIX_THROUGHPUT_KWH]
            * experiment[item + SUFFIX_COST_VAR]
        )

    # include opex costs
    for item in component_list:
        if item == STORAGE:
            om += (
                experiment[SHORTAGE_CAPACITY_COST_OPEX]
                * experiment[STORAGE_CAPACITY_LIFETIME]
            )
            om += (
                experiment[STORAGE_POWER_COST_OPEX] * experiment[STORAGE_POWER_LIFETIME]
            )
        else:
            om += experiment[item + SUFFIX_COST_OPEX] * experiment[item + SUFFIX_LIFETIME]

    oemof_results.update({OPERATION_MAINTAINANCE_EXPENDITURES: om})

    logging.debug("Economic evaluation. Scaling investment costs and O&M to year.")

    for item in component_list:

        if item in [PROJECT, MAINGRID_EXTENSION, DISTRIBUTION_GRID]:
            oemof_results.update(
                {
                    PREFIX_ANNUITY
                    + item: (interval_annuity[PREFIX_ANNUITY + item]) * 365 / evaluated_days
                }
            )
        else:
            oemof_results.update(
                {
                    PREFIX_ANNUITY
                    + item: (
                        interval_annuity[PREFIX_ANNUITY + item]
                        + om_var_interval[PREFIX_OM_VAR + item]
                    )
                    * 365
                    / evaluated_days
                }
            )

    oemof_results.update({ANNUITY: 0})

    for item in component_list:
        oemof_results.update(
            {ANNUITY: oemof_results[ANNUITY] + oemof_results[PREFIX_ANNUITY + item]}
        )

    return


def costs(oemof_results, experiment):
    logging.debug("Economic evaluation. Calculating present costs.")

    component_list = [
        PV,
        WIND,
        GENSET,
        STORAGE,
        PCOUPLING,
        MAINGRID_EXTENSION,
        DISTRIBUTION_GRID,
        RECTIFIER_AC_DC,
        INVERTER_DC_AC,
        PROJECT,
    ]

    for item in component_list:
        oemof_results.update(
            {
                PREFIX_COSTS
                + item: oemof_results[PREFIX_ANNUITY + item] * experiment[ANNUITY_FACTOR]
            }
        )

    return


def calculate_co2_emissions(oemof_results, experiment):
    co2_emissions = 0
    if CONSUMPTION_FUEL_ANNUAL_L in oemof_results:
        co2_emissions += (
            oemof_results[CONSUMPTION_FUEL_ANNUAL_L]
            * experiment[FUEL_CO2_EMISSION_FACTOR]
        )
    if "consumption_main_grid_utility_side_annual_kWh" in oemof_results:
        co2_emissions += (
            oemof_results["consumption_main_grid_utility_side_annual_kWh"]
            * experiment["maingrid_co2_emission_factor"]
        )
    oemof_results.update({CO2_EMISSIONS_KGC02EQ: co2_emissions})
    logging.debug("Calculated CO2 emissions.")
    return


def expenditures_fuel(oemof_results, experiment):
    logging.debug("Economic evaluation. Calculating fuel consumption and expenditures.")
    oemof_results.update(
        {
            CONSUMPTION_FUEL_ANNUAL_L: oemof_results[CONSUMPTION_FUEL_ANNUAL_KWH]
            / experiment[COMBUSTION_VALUE_FUEL]
        }
    )

    oemof_results.update(
        {
            EXPENDITURES_FUEL_ANNUAL: oemof_results[CONSUMPTION_FUEL_ANNUAL_L]
            * experiment[PRICE_FUEL]
        }
    )

    oemof_results.update(
        {
            OPERATION_MAINTAINANCE_EXPENDITURES: oemof_results[
                OPERATION_MAINTAINANCE_EXPENDITURES
            ]
            + oemof_results[EXPENDITURES_FUEL_ANNUAL]
        }
    )

    oemof_results.update(
        {
            EXPENDITURES_FUEL_TOTAL: oemof_results[EXPENDITURES_FUEL_ANNUAL]
            * experiment[ANNUITY_FACTOR]
        }
    )

    oemof_results.update(
        {ANNUITY: oemof_results[ANNUITY] + oemof_results[EXPENDITURES_FUEL_ANNUAL]}
    )
    return


def expenditures_main_grid_consumption(oemof_results, experiment):
    logging.debug(
        "Economic evaluation. Calculating main grid consumption and expenditures."
    )
    # Necessary in oemof_results: consumption_main_grid_annual
    oemof_results.update(
        {
            EXPENDITURES_MAIN_GRID_CONSUMPTION_ANNUAL: oemof_results[
                CONSUMPTION_MAIN_GRID_MG_SIDE_ANNUAL_KWH
            ]
            * experiment[MAINGRID_ELECTRICITY_PRICE]
        }
    )

    oemof_results.update(
        {
            OPERATION_MAINTAINANCE_EXPENDITURES: oemof_results[
                OPERATION_MAINTAINANCE_EXPENDITURES
            ]
            + oemof_results[EXPENDITURES_MAIN_GRID_CONSUMPTION_ANNUAL]
        }
    )

    oemof_results.update(
        {
            EXPENDITURES_MAIN_GRID_CONSUMPTION_TOTAL: oemof_results[
                EXPENDITURES_MAIN_GRID_CONSUMPTION_ANNUAL
            ]
            * experiment[ANNUITY_FACTOR]
        }
    )

    oemof_results.update(
        {
            ANNUITY: oemof_results[ANNUITY]
            + oemof_results[EXPENDITURES_MAIN_GRID_CONSUMPTION_ANNUAL]
        }
    )
    return


def expenditures_shortage(oemof_results, experiment):
    logging.debug("Economic evaluation. Calculating shortage and expenditures.")
    # Necessary in oemof_results: consumption_main_grid_annual
    oemof_results.update(
        {
            EXPENDITURES_SHORTAGE_ANNUAL: oemof_results[
                TOTAL_DEMAND_SHORTAGE_ANNUAL_KWH
            ]
            * experiment[SHORTAGE_PENALTY_COST]
        }
    )

    oemof_results.update(
        {
            OPERATION_MAINTAINANCE_EXPENDITURES: oemof_results[
                OPERATION_MAINTAINANCE_EXPENDITURES
            ]
            + oemof_results[EXPENDITURES_SHORTAGE_ANNUAL]
        }
    )

    oemof_results.update(
        {
            EXPENDITURES_SHORTAGE_TOTAL: oemof_results[EXPENDITURES_SHORTAGE_ANNUAL]
            * experiment[ANNUITY_FACTOR]
        }
    )

    if experiment["include_shortage_penalty_costs_in_lcoe"] == True:
        oemof_results.update(
            {
                ANNUITY: oemof_results[ANNUITY]
                + oemof_results[EXPENDITURES_SHORTAGE_ANNUAL]
            }
        )
    else:
        oemof_results.update(
            {
                COMMENTS: oemof_results[COMMENTS]
                + "Shortage penalty costs used in OEM not included in LCOE. "
            }
        )
    return


def revenue_main_grid_feedin(oemof_results, experiment):
    logging.debug("Economic evaluation. Calculating feeding and revenues.")
    oemof_results.update(
        {
            REVENUE_MAIN_GRID_FEEDIN_ANNUAL: -oemof_results[
                FEEDIN_MAIN_GRID_MG_SIDE_ANNUAL_KWH
            ]
            * experiment[MAINGRID_FEEDIN_TARIFF]
        }
    )

    oemof_results.update(
        {
            REVENUE_MAIN_GRID_FEEDIN_TOTAL: oemof_results[
                REVENUE_MAIN_GRID_FEEDIN_ANNUAL
            ]
            * experiment[ANNUITY_FACTOR]
        }
    )

    oemof_results.update(
        {
            ANNUITY: oemof_results[ANNUITY]
            + oemof_results[REVENUE_MAIN_GRID_FEEDIN_ANNUAL]
        }
    )
    return


def annual_value(value, evaluated_days):
    value = value * 365 / evaluated_days
