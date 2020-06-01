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
        {"npv": oemof_results["annuity"] * experiment["annuity_factor"]}
    )

    if oemof_results["total_demand_supplied_annual_kWh"] > 0:
        oemof_results.update(
            {
                "lcoe": oemof_results["annuity"]
                / oemof_results["total_demand_supplied_annual_kWh"]
            }
        )
    else:
        oemof_results.update({"lcoe": 0})
    return

def annuities_365(case_dict, oemof_results, experiment):
    evaluated_days = case_dict["evaluated_days"]

    logging.debug(
        "Economic evaluation. Calculating investment costs over analysed timeframe."
    )

    interval_annuity = {
        "annuity_pv": experiment["pv_cost_annuity"]
        * oemof_results["capacity_pv_kWp"],
        "annuity_wind": experiment["wind_cost_annuity"]
        * oemof_results["capacity_wind_kW"],
        "annuity_storage": experiment["storage_capacity_cost_annuity"]
        * oemof_results["capacity_storage_kWh"]
        + experiment["storage_power_cost_annuity"]
        * oemof_results["power_storage_kW"],
        "annuity_genset": experiment["genset_cost_annuity"]
        * oemof_results["capacity_genset_kW"],
        "annuity_rectifier_ac_dc": experiment["rectifier_ac_dc_cost_annuity"]
        * oemof_results["capacity_rectifier_ac_dc_kW"],
        "annuity_inverter_dc_ac": experiment["inverter_dc_ac_cost_annuity"]
        * oemof_results["capacity_inverter_dc_ac_kW"],
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
                * oemof_results["capacity_pcoupling_kW"]
            }
        )
    else:
        interval_annuity.update(
            {
                "annuity_pcoupling": experiment["pcoupling_cost_annuity"]
                * oemof_results["capacity_pcoupling_kW"]
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
                * experiment["maingrid_distance"]
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
                experiment["pv_cost_investment"] * oemof_results["capacity_pv_kWp"]
            )
        elif item == "storage":
            investment += (
                experiment["storage_capacity_cost_investment"]
                * oemof_results["capacity_storage_kWh"]
            )
            investment += (
                experiment["storage_power_cost_investment"]
                * oemof_results["capacity_storage_kWh"]
            )
        elif item == "maingrid_extension":
            investment += (
                experiment["maingrid_extension_cost_investment"]
                * experiment["maingrid_distance"]
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
                experiment["storage_capacity_cost_opex"]
                * experiment["storage_capacity_lifetime"]
            )
            om += (
                experiment["storage_power_cost_opex"]
                * experiment["storage_power_lifetime"]
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

    oemof_results.update({"annuity": 0})

    for item in component_list:
        oemof_results.update(
            {"annuity": oemof_results["annuity"] + oemof_results["annuity_" + item]}
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
            "consumption_fuel_annual_l": oemof_results[
                "consumption_fuel_annual_kWh"
            ]
            / experiment["combustion_value_fuel"]
        }
    )
    oemof_results.update(
        {
            "expenditures_fuel_annual": oemof_results["consumption_fuel_annual_l"]
            * experiment["price_fuel"]
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
            "annuity": oemof_results["annuity"]
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
                "consumption_main_grid_mg_side_annual_kWh"
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
            "annuity": oemof_results["annuity"]
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
                "total_demand_shortage_annual_kWh"
            ]
            * experiment["shortage_penalty_costs"]
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
                "annuity": oemof_results["annuity"]
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
                "feedin_main_grid_mg_side_annual_kWh"
            ]
            * experiment["maingrid_feedin_tariff"]
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
            "annuity": oemof_results["annuity"]
            + oemof_results["revenue_main_grid_feedin_annual"]
        }
    )
    return

def annual_value(value, evaluated_days):
    value = value * 365 / evaluated_days
