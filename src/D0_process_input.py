"""
Small scripts to keep the main file clean
"""

import pandas as pd
import sys
import logging

try:
    import src.D1_economic_functions as economics
except ModuleNotFoundError:
    print("Module error at D0")
    import src.D1_economic_functions as economics

def list_of_cases(case_definitions):
    case_list = []
    str_cases_simulated = ""
    # Certain ORDER of simulation: First base capacities are optimized
    for case in case_definitions:
        if (
            case_definitions[case]["perform_simulation"] == True
            and case_definitions[case]["based_on_case"] == False
        ):
            case_list.append(case)
            str_cases_simulated += case + ", "

    logging.info("Base capacities provided by: " + str_cases_simulated[:-2])

    for case in case_definitions:
        if (
            case_definitions[case]["perform_simulation"] == True
            and case_definitions[case]["based_on_case"] == True
        ):
            case_list.append(case)
            str_cases_simulated += case + ", "

        if len(case_list) == 0:
            logging.error(
                "No cases defined to be simulated. \n "
                'Did you set any "perform_simulation"=True in excel template, tab CASE_DEFINITIONS?'
            )
            sys.exit()

    logging.info("All simulated cases: " + str_cases_simulated[:-2])
    return case_list

def economic_values(experiment):
    """Pre-processing of input data (calculation of economic values)"""
    experiment.update(
        {
            "annuity_factor": economics.annuity_factor(
                experiment["project_lifetime"], experiment["wacc"]
            )
        }
    )
    experiment.update(
        {"crf": economics.crf(experiment["project_lifetime"], experiment["wacc"])}
    )

    if "price_fuel" not in experiment:
        present_value_changing_fuel_price = economics.present_value_of_changing_fuel_price(
            experiment["fuel_price"],
            experiment["project_lifetime"],
            experiment["wacc"],
            experiment["fuel_price_change_annual"],
            experiment["crf"],
        )
        experiment.update({"price_fuel": present_value_changing_fuel_price})
    else:
        logging.warning(
            'You used decrepated value "price_fuel" in your excel input file. \n '
            + "    "
            + "    "
            + "    "
            + 'This still works, but with values "fuel_price" and "fuel_price_change_annual" you could take into account price changes.'
        )

    component_list = [
        "pv",
        "wind",
        "genset",
        "storage_capacity",
        "storage_power",
        "pcoupling",
        "maingrid_extension",
        "distribution_grid",
        "rectifier_ac_dc",
        "inverter_dc_ac",
        "project",
    ]

    for item in component_list:
        # --------------------------------------------------#
        # CAPEX without opex/a                              #
        # --------------------------------------------------#
        experiment.update(
            {
                item
                + "_cost_capex": economics.capex_from_investment(
                    experiment[item + "_cost_investment"],
                    experiment[item + "_lifetime"],
                    experiment["project_lifetime"],
                    experiment["wacc"],
                    experiment["tax"],
                )
            }
        )

        # --------------------------------------------------#
        # Annuities of components including opex AND capex #
        # --------------------------------------------------#
        experiment.update(
            {
                item
                + "_cost_annuity": economics.annuity(
                    experiment[item + "_cost_capex"], experiment["crf"]
                )
                + experiment[item + "_cost_opex"]
            }
        )

        # --------------------------------------------------#
        # Scaling annuity to timeframe                      #
        # --------------------------------------------------#
        # Updating all annuities above to annuities "for the timeframe", so that optimization is based on more adequate
        # costs. Includes project_cost_annuity, distribution_grid_cost_annuity, maingrid_extension_cost_annuity for
        # consistency eventhough these are not used in optimization.
        experiment.update(
            {
                item
                + "_cost_annuity": experiment[item + "_cost_annuity"]
                / 365
                * experiment["evaluated_days"]
            }
        )

    return experiment

def add_timeseries(experiment_s):
    # Update experiments and add longest date_time_index to settings
    entries = 0
    longest = ""

    for experiment in experiment_s:
        experiment_s[experiment].update(
            {
                "time_end": experiment_s[experiment]["time_start"]
                + pd.DateOffset(days=experiment_s[experiment]["evaluated_days"])
                - pd.DateOffset(hours=1)
            }
        )
        # experiment_s[experiment].update({'time_end': experiment_s[experiment]['time_start']+ pd.DateOffset(hours=2)})
        experiment_s[experiment].update(
            {
                "date_time_index": pd.date_range(
                    start=experiment_s[experiment]["time_start"],
                    end=experiment_s[experiment]["time_end"],
                    freq=experiment_s[experiment]["time_frequency"],
                )
            }
        )

        if len(experiment_s[experiment]["date_time_index"]) > entries:
            entries = len(experiment_s[experiment]["date_time_index"])
            longest = experiment

    max_date_time_index = experiment_s[longest]["date_time_index"]
    max_evaluated_days = experiment_s[longest]["evaluated_days"]

    for experiment in experiment_s:
        index = experiment_s[experiment]["date_time_index"]
        if experiment_s[experiment]["file_index"] != None:
            if DEMAND_AC in experiment_s[experiment]:
                year_timeseries_in_file = (
                    experiment_s[experiment][DEMAND_AC].index[0].year
                )
            else:
                year_timeseries_in_file = (
                    experiment_s[experiment][DEMAND_DC].index[0].year
                )

            if (
                experiment_s[experiment]["date_time_index"][0].year
                != year_timeseries_in_file
            ):
                file_index = [
                    item + pd.DateOffset(year=index[0].year)
                    for item in index
                ]
                # shift to fileindex of data sets to analysed year
                demand_ac = pd.Series(
                    experiment_s[experiment][DEMAND_AC].values,
                    index=experiment_s[experiment]["file_index"],
                )
                demand_dc = pd.Series(
                    experiment_s[experiment][DEMAND_DC].values,
                    index=experiment_s[experiment]["file_index"],
                )
                pv_generation_per_kWp = pd.Series(
                    experiment_s[experiment][PV_GENERATION_PER_KWP].values,
                    index=experiment_s[experiment]["file_index"],
                )
                wind_generation_per_kW = pd.Series(
                    experiment_s[experiment]["wind_generation_per_kW"].values,
                    index=experiment_s[experiment]["file_index"],
                )
                # from provided data use only analysed timeframe
                experiment_s[experiment].update(
                    {"demand_profile_ac": demand_ac[index]}
                )
                experiment_s[experiment].update(
                    {"demand_profile_dc": demand_dc[index]}
                )
                experiment_s[experiment].update(
                    {PV_GENERATION_PER_KWP: pv_generation_per_kWp[index]}
                )
                experiment_s[experiment].update(
                    {"wind_generation_per_kW": wind_generation_per_kW[index]}
                )

                if "grid_availability" in experiment_s[experiment].keys():
                    grid_availability = pd.Series(
                        experiment_s[experiment]["grid_availability"].values,
                        index=experiment_s[experiment]["file_index"],
                    )
                    experiment_s[experiment].update(
                        {"grid_availability": grid_availability[index]}
                    )

            else:
                # file index is date time index, no change necessary
                pass

        elif experiment_s[experiment]["file_index"] == None:
            # limit based on index
            experiment_s[experiment].update(
                {
                    "demand_profile_ac": pd.Series(
                        experiment_s[experiment][DEMAND_AC][
                            0 : len(index)
                        ].values,
                        index=index,
                    )
                }
            )
            experiment_s[experiment].update(
                {
                    "demand_profile_dc": pd.Series(
                        experiment_s[experiment][DEMAND_DC][
                            0 : len(index)
                        ].values,
                        index=index,
                    )
                }
            )
            experiment_s[experiment].update(
                {
                    PV_GENERATION_PER_KWP: pd.Series(
                        experiment_s[experiment][PV_GENERATION_PER_KWP][
                            0 : len(index)
                        ].values,
                        index=index,
                    )
                }
            )
            experiment_s[experiment].update(
                {
                    "wind_generation_per_kW": pd.Series(
                        experiment_s[experiment]["wind_generation_per_kW"][
                            0 : len(index)
                        ].values,
                        index=index,
                    )
                }
            )

            if "grid_availability" in experiment_s[experiment].keys():
                experiment_s[experiment].update(
                    {
                        "grid_availability": pd.Series(
                            experiment_s[experiment]["grid_availability"][
                                0 : len(index)
                            ].values,
                            index=index,
                        )
                    }
                )

        else:
            logging.warning(
                'Project site value "file_index" neither None not non-None.'
            )

        # Used for generation of lp file with only 3-timesteps = Useful to verify optimized equations
        if experiment_s[experiment]["lp_file_for_only_3_timesteps"] == True:
            experiment_s[experiment].update(
                {
                    "time_start": experiment_s[experiment]["time_start"]
                    + pd.DateOffset(hours=15)
                }
            )
            experiment_s[experiment].update(
                {
                    "time_end": experiment_s[experiment]["time_start"]
                    + pd.DateOffset(hours=2)
                }
            )
            experiment_s[experiment].update(
                {
                    "date_time_index": pd.date_range(
                        start=experiment_s[experiment]["time_start"],
                        end=experiment_s[experiment]["time_end"],
                        freq=experiment_s[experiment]["time_frequency"],
                    )
                }
            )

            index = experiment_s[experiment]["date_time_index"]
            experiment_s[experiment].update(
                {
                    "demand_profile_ac": experiment_s[experiment][
                        "demand_profile_ac"
                    ][index]
                }
            )
            experiment_s[experiment].update(
                {
                    "demand_profile_dc": experiment_s[experiment][
                        "demand_profile_dc"
                    ][index]
                }
            )
            experiment_s[experiment].update(
                {
                    PV_GENERATION_PER_KWP: experiment_s[experiment][
                        PV_GENERATION_PER_KWP
                    ][index]
                }
            )
            experiment_s[experiment].update(
                {
                    "wind_generation_per_kW": experiment_s[experiment][
                        "wind_generation_per_kW"
                    ][index]
                }
            )
            if "grid_availability" in experiment_s[experiment].keys():
                experiment_s[experiment].update(
                    {
                        "grid_availability": experiment_s[experiment][
                            "grid_availability"
                        ][index]
                    }
                )

        experiment_s[experiment].update(
            {
                "accumulated_profile_ac_side": experiment_s[experiment][
                    "demand_profile_ac"
                ]
                + experiment_s[experiment]["demand_profile_dc"]
                / experiment_s[experiment]["rectifier_ac_dc_efficiency"]
            }
        )

        experiment_s[experiment].update(
            {
                "accumulated_profile_dc_side": experiment_s[experiment][
                    "demand_profile_ac"
                ]
                / experiment_s[experiment]["inverter_dc_ac_efficiency"]
                + experiment_s[experiment]["demand_profile_dc"]
            }
        )
        experiment_s[experiment].update(
            {
                "total_demand_ac": sum(
                    experiment_s[experiment]["demand_profile_ac"]
                ),
                "peak_demand_ac": max(
                    experiment_s[experiment]["demand_profile_ac"]
                ),
                "total_demand_dc": sum(
                    experiment_s[experiment]["demand_profile_dc"]
                ),
                "peak_demand_dc": max(
                    experiment_s[experiment]["demand_profile_dc"]
                ),
                "peak_pv_generation_per_kWp": max(
                    experiment_s[experiment][PV_GENERATION_PER_KWP]
                ),
                "peak_wind_generation_per_kW": max(
                    experiment_s[experiment]["wind_generation_per_kW"]
                ),
            }
        )

        experiment_s[experiment].update(
            {
                "mean_demand_ac": experiment_s[experiment]["total_demand_ac"]
                / len(experiment_s[experiment]["date_time_index"]),
                "mean_demand_dc": experiment_s[experiment]["total_demand_dc"]
                / len(experiment_s[experiment]["date_time_index"]),
            }
        )

        if experiment_s[experiment]["mean_demand_ac"] > 0:
            experiment_s[experiment].update(
                {
                    "peak/mean_demand_ratio_ac": experiment_s[experiment][
                        "peak_demand_ac"
                    ]
                    / experiment_s[experiment]["mean_demand_ac"]
                }
            )
        else:
            experiment_s[experiment].update({"peak/mean_demand_ratio_ac": 0})

        if experiment_s[experiment]["mean_demand_dc"] > 0:
            experiment_s[experiment].update(
                {
                    "peak/mean_demand_ratio_dc": experiment_s[experiment][
                        "peak_demand_dc"
                    ]
                    / experiment_s[experiment]["mean_demand_dc"]
                }
            )
        else:
            experiment_s[experiment].update({"peak/mean_demand_ratio_dc": 0})

        # Used for estimation of capacities using "peak demand"
        experiment_s[experiment].update(
            {
                "abs_peak_demand_ac_side": max(
                    experiment_s[experiment]["accumulated_profile_ac_side"]
                )
            }
        )

        # Warnings
        if (
            experiment_s[experiment]["total_demand_ac"]
            == 0 + experiment_s[experiment]["total_demand_dc"]
            == 0
        ):
            logging.warning(
                "No demand in evaluated timesteps at project site "
                + experiment_s[experiment]["project_site_name"]
                + " - simulation will crash."
            )
        if experiment_s[experiment]["peak_pv_generation_per_kWp"] == 0:
            logging.info(
                "No pv generation in evaluated timesteps at project site "
                + experiment_s[experiment]["project_site_name"]
                + "."
            )
        if experiment_s[experiment]["peak_wind_generation_per_kW"] == 0:
            logging.info(
                "No wind generation in evaluated timesteps at project site "
                + experiment_s[experiment]["project_site_name"]
                + "."
            )

    return max_date_time_index, max_evaluated_days

def apply_noise(experiment_s):
    for experiment in experiment_s:
        on_series(experiment_s[experiment], "white_noise_demand", DEMAND_AC)
        on_series(experiment_s[experiment], "white_noise_demand", DEMAND_DC)
        on_series(
            experiment_s[experiment], "white_noise_pv", PV_GENERATION_PER_KWP
        )
        on_series(
            experiment_s[experiment], "white_noise_wind", "wind_generation_per_kW"
        )
    return

def on_series(experiment, noise_name, series_name):
    if experiment[noise_name] != 0:
        series_values = pd.Series(
            randomized(experiment[noise_name], experiment[series_name]),
            index=experiment[series_name].index,
        )
        experiment.update({series_name: series_values})
        # add display of series with noise
    return

def randomized(white_noise_percentage, data_subframe):
    import numpy as np

    noise = np.random.normal(0, white_noise_percentage, len(data_subframe))
    for i in range(0, len(data_subframe)):
        if data_subframe[i] != 0:
            data_subframe[i] = data_subframe[i] * (1 - noise[i])
    return data_subframe.clip_lower(0)  # do not allow values <0
