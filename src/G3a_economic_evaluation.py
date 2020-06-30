###############################################################################
# Imports and initialize
###############################################################################

import logging

# Try to import matplotlib librar
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

    if case_dict["pcc_consumption_fixed_capacity"] != None:
        # ---------Expenditures from electricity consumption from main grid ----------#
        expenditures_main_grid_consumption(
            oemof_results, experiment
        )

    if case_dict["pcc_feedin_fixed_capacity"] != None:
        # ---------Revenues from electricity feed-in to main grid ----------#
        revenue_main_grid_feedin(oemof_results, experiment)

    oemof_results.update(
        {NPV: oemof_results[ANNUITY] * experiment["annuity_factor"]}
    )

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
    evaluated_days = case_dict["evaluated_days"]

    logging.debug(
        "Economic evaluation. Calculating investment costs over analysed timeframe."
    )

    interval_annuity = {
        ANNUITY_PV: experiment["pv_cost_annuity"]
        * oemof_results[CAPACITY_PV_KWP],
        ANNUITY_WIND: experiment["wind_cost_annuity"]
        * oemof_results[CAPACITY_WIND_KW],
        ANNUITY_STORAGE: experiment["storage_capacity_cost_annuity"]
        * oemof_results[CAPACITY_STORAGE_KWH]
        + experiment["storage_power_cost_annuity"]
        * oemof_results[POWER_STORAGE_KW],
        "annuity_genset": experiment["genset_cost_annuity"]
        * oemof_results[CAPACITY_GENSET_KW],
        ANNUITY_RECTIFIER_AC_DC: experiment["rectifier_ac_dc_cost_annuity"]
        * oemof_results[CAPACITY_RECTIFIER_AC_DC_KW],
        ANNUITY_INVERTER_DC_AC: experiment["inverter_dc_ac_cost_annuity"]
        * oemof_results[CAPACITY_INVERTER_DC_AC_KW],
    }

    list_fix = ["project", "distribution_grid"]
    for item in list_fix:
        interval_annuity.update(
            {"annuity_" + item: experiment[item + "_cost_annuity"]}
        )

    if (
        case_dict["pcc_consumption_fixed_capacity"] != None
        and case_dict["pcc_feedin_fixed_capacity"] != None
    ):
        interval_annuity.update(
            {
                "annuity_pcoupling": 2
                * experiment["pcoupling_cost_annuity"]
                * oemof_results[CAPACITY_PCOUPLING_KW]
            }
        )
    else:
        interval_annuity.update(
            {
                "annuity_pcoupling": experiment["pcoupling_cost_annuity"]
                * oemof_results[CAPACITY_PCOUPLING_KW]
            }
        )

    # Main grid extension
    if (
        case_dict["pcc_consumption_fixed_capacity"] != None
        or case_dict["pcc_feedin_fixed_capacity"] != None
    ):
        interval_annuity.update(
            {
                "annuity_maingrid_extension": experiment[
                    "maingrid_extension_cost_annuity"
                ]
                * experiment[MAINGRID_DISTANCE]
            }
        )
    else:
        interval_annuity.update({"annuity_maingrid_extension": 0})

    component_list = [
        "pv",
        "wind",
        "genset",
        "storage",
        "pcoupling",
        "maingrid_extension",
        "distribution_grid",
        "rectifier_ac_dc",
        "inverter_dc_ac",
        "project",
    ]

    # include in oemof_results just first investment costs
    investment = 0
    for item in component_list:
        if item == "pv":
            investment += (
                experiment[PV_COST_INVESTMENT] * oemof_results[CAPACITY_PV_KWP]
            )
        elif item == "storage":
            investment += (
                experiment[SHORTAGE_CAPACITY_COST_INVESTMENT]
                * oemof_results[CAPACITY_STORAGE_KWH]
            )
            investment += (
                experiment[STORAGE_POWER_COST_INVESTMENT ]
                * oemof_results[CAPACITY_STORAGE_KWH]
            )
        elif item == "maingrid_extension":
            investment += (
                experiment[MAINGRID_ELECTRICITY_COST_INVESTMENT]
                * experiment[MAINGRID_DISTANCE]
            )
        elif item in ["distribution_grid", "project"]:
            investment += experiment[item + "_cost_investment"]
        else:
            investment += (
                experiment[item + "_cost_investment"]
                * oemof_results["capacity_" + item + "_kW"]
            )

    oemof_results.update({"first_investment": investment})

    logging.debug(
        "Economic evaluation. Calculating O&M costs over analysed timeframe."
    )

    om_var_interval = {}
    om = (
        0  # first, var costs are included, then opex costs and finally expenditures
    )
    for item in ["pv", "wind", "genset"]:
        om_var_interval.update(
            {
                "om_var_"
                + item: oemof_results["total_" + item + "_generation_kWh"]
                * experiment[item + "_cost_var"]
            }
        )
        om += (
            oemof_results["total_" + item + "_generation_kWh"]
            * experiment[item + "_cost_var"]
        )

    for item in ["pcoupling", "storage", "rectifier_ac_dc", "inverter_dc_ac"]:
        om_var_interval.update(
            {
                "om_var_"
                + item: oemof_results["total_" + item + "_throughput_kWh"]
                * experiment[item + "_cost_var"]
            }
        )
        om += (
            oemof_results["total_" + item + "_throughput_kWh"]
            * experiment[item + "_cost_var"]
        )

    # include opex costs
    for item in component_list:
        if item == "storage":
            om += (
                experiment[SHORTAGE_CAPACITY_COST_OPEX]
                * experiment[STORAGE_CAPACITY_LIFETIME]
            )
            om += (
                experiment[STORAGE_POWER_COST_OPEX]
                * experiment[STORAGE_POWER_LIFETIME]
            )
        else:
            om += experiment[item + "_cost_opex"] * experiment[item + "_lifetime"]

    oemof_results.update({"operation_mantainance_expenditures": om})

    logging.debug("Economic evaluation. Scaling investment costs and O&M to year.")

    for item in component_list:

        if item in ["project", "maingrid_extension", "distribution_grid"]:
            oemof_results.update(
                {
                    "annuity_"
                    + item: (interval_annuity["annuity_" + item])
                    * 365
                    / evaluated_days
                }
            )
        else:
            oemof_results.update(
                {
                    "annuity_"
                    + item: (
                        interval_annuity["annuity_" + item]
                        + om_var_interval["om_var_" + item]
                    )
                    * 365
                    / evaluated_days
                }
            )

    oemof_results.update({ANNUITY: 0})

    for item in component_list:
        oemof_results.update(
            {ANNUITY: oemof_results[ANNUITY] + oemof_results["annuity_" + item]}
        )

    return

def costs(oemof_results, experiment):
    logging.debug("Economic evaluation. Calculating present costs.")

    component_list = [
        "pv",
        "wind",
        "genset",
        "storage",
        "pcoupling",
        "maingrid_extension",
        "distribution_grid",
        "rectifier_ac_dc",
        "inverter_dc_ac",
        "project",
    ]

    for item in component_list:
        oemof_results.update(
            {
                "costs_"
                + item: oemof_results["annuity_" + item]
                * experiment["annuity_factor"]
            }
        )

    return

def expenditures_fuel(oemof_results, experiment):
    logging.debug(
        "Economic evaluation. Calculating fuel consumption and expenditures."
    )
    oemof_results.update(
        {
            CONSUMPTION_FUEL_ANNUAL_L: oemof_results[
                "consumption_fuel_annual_kWh"
            ]
            / experiment[COMBUSTION_VALUE_FUEL]
        }
    )
    oemof_results.update(
        {
            "expenditures_fuel_annual": oemof_results[CONSUMPTION_FUEL_ANNUAL_L]
            * experiment[PRICE_FUEL]
        }
    )

    oemof_results.update(
        {
            "operation_mantainance_expenditures": oemof_results[
                "operation_mantainance_expenditures"
            ]
            + oemof_results["expenditures_fuel_annual"]
        }
    )

    oemof_results.update(
        {
            "expenditures_fuel_total": oemof_results["expenditures_fuel_annual"]
            * experiment["annuity_factor"]
        }
    )

    oemof_results.update(
        {
            ANNUITY: oemof_results[ANNUITY]
            + oemof_results["expenditures_fuel_annual"]
        }
    )
    return

def expenditures_main_grid_consumption(oemof_results, experiment):
    logging.debug(
        "Economic evaluation. Calculating main grid consumption and expenditures."
    )
    # Necessary in oemof_results: consumption_main_grid_annual
    oemof_results.update(
        {
            "expenditures_main_grid_consumption_annual": oemof_results[
                CONSUMPTION_MAIN_GRID_MG_SIDE_ANNUAL_KWH
            ]
            * experiment["maingrid_electricity_price"]
        }
    )

    oemof_results.update(
        {
            "operation_mantainance_expenditures": oemof_results[
                "operation_mantainance_expenditures"
            ]
            + oemof_results["expenditures_main_grid_consumption_annual"]
        }
    )

    oemof_results.update(
        {
            "expenditures_main_grid_consumption_total": oemof_results[
                "expenditures_main_grid_consumption_annual"
            ]
            * experiment["annuity_factor"]
        }
    )

    oemof_results.update(
        {
            ANNUITY: oemof_results[ANNUITY]
            + oemof_results["expenditures_main_grid_consumption_annual"]
        }
    )
    return

def expenditures_shortage(oemof_results, experiment):
    logging.debug("Economic evaluation. Calculating shortage and expenditures.")
    # Necessary in oemof_results: consumption_main_grid_annual
    oemof_results.update(
        {
            "expenditures_shortage_annual": oemof_results[
                TOTAL_DEMAND_SHORTAGE_ANNUAL_KWH
            ]
            * experiment[SHORTAGE_PENALTY_COST]
        }
    )

    oemof_results.update(
        {
            "operation_mantainance_expenditures": oemof_results[
                "operation_mantainance_expenditures"
            ]
            + oemof_results["expenditures_shortage_annual"]
        }
    )

    oemof_results.update(
        {
            "expenditures_shortage_total": oemof_results[
                "expenditures_shortage_annual"
            ]
            * experiment["annuity_factor"]
        }
    )

    if experiment["include_shortage_penalty_costs_in_lcoe"] == True:
        oemof_results.update(
            {
                ANNUITY: oemof_results[ANNUITY]
                + oemof_results["expenditures_shortage_annual"]
            }
        )
    else:
        oemof_results.update(
            {
                "comments": oemof_results["comments"]
                + "Shortage penalty costs used in OEM not included in LCOE. "
            }
        )
    return

def revenue_main_grid_feedin(oemof_results, experiment):
    logging.debug("Economic evaluation. Calculating feeding and revenues.")
    oemof_results.update(
        {
            "revenue_main_grid_feedin_annual": -oemof_results[
                FEEDIN_MAIN_GRID_MG_SIDE_ANNUAL_KWH
            ]
            * experiment[MAINGRID_FEEDIN_TARIFF]
        }
    )

    oemof_results.update(
        {
            "revenue_main_grid_feedin_total": oemof_results[
                "revenue_main_grid_feedin_annual"
            ]
            * experiment["annuity_factor"]
        }
    )

    oemof_results.update(
        {
            ANNUITY: oemof_results[ANNUITY]
            + oemof_results["revenue_main_grid_feedin_annual"]
        }
    )
    return

def annual_value(value, evaluated_days):
    value = value * 365 / evaluated_days
