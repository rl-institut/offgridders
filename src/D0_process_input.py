"""
Small scripts to keep the main file clean
"""

import pandas as pd
import sys
import logging
import src.D1_economic_functions as economics

import src.D1_economic_functions as economics

from src.constants import (
    PERFORM_SIMULATION,
    BASED_ON_CASE,
    ANNUITY_FACTOR,
    CRF,
    PV,
    WIND,
    GENSET,
    STORAGE_CAPACITY,
    STORAGE_POWER,
    PCOUPLING,
    MAINGRID_EXTENSION,
    DISTRIBUTION_GRID,
    RECTIFIER_AC_DC,
    INVERTER_DC_AC,
    PROJECT,
    EVALUATED_DAYS,
    TIME_END,
    TIME_START,
    DATE_TIME_INDEX,
    TIME_FREQUENCY,
    FILE_INDEX,
    DEMAND_PROFILE_AC,
    DEMAND_PROFILE_DC,
    ACCUMULATED_PROFILE_AC_SIDE,
    ACCUMULATED_PROFILE_DC_SIDE,
    TOTAL_DEMAND_AC,
    PEAK_DEMAND_AC,
    TOTAL_DEMAND_DC,
    PEAK_DEMAND_DC,
    PEAK_PV_GENERATION_PER_KWP,
    PEAK_WIND_GENERATION_PER_KW,
    MEAN_DEMAND_AC,
    MEAN_DEMAND_DC,
    PEAK_MEAN_DEMAND_RATIO_AC,
    PEAK_MEAN_DEMAND_RATIO_DC,
    ABS_PEAK_DEMAND_AC_SIDE,
    PROJECT_LIFETIME,
    WACC,
    PRICE_FUEL,
    FUEL_PRICE,
    FUEL_PRICE_CHANGE_ANNUAL,
    TAX,
    DEMAND_AC,
    PV_GENERATION_PER_KWP,
    WIND_GENERATION_PER_KW,
    GRID_AVAILABILITY,
    DEMAND_DC,
    LP_FILE_FOR_ONLY_3_TIMESTEPS,
    RECTIFIER_AC_DC_EFFICIENCY,
    INVERTER_DC_AC_EFFICIENCY,
    PROJECT_SITE_NAME,
    WHITE_NOISE_DEMAND,
    WHITE_NOISE_PV,
    WHITE_NOISE_WIND,
    SUFFIX_COST_INVESTMENT,
    SUFFIX_LIFETIME,
    SUFFIX_COST_OPEX,
    SUFFIX_COST_ANNUITY,
    SUFFIX_COST_CAPEX,
)


def list_of_cases(case_definitions):
    """
    Creates a list for the simulation order of different cases.

    Cases that provide the base capacities for other cases should be simulated first.

    Parameters
    ----------
    case_definitions: dict of dicts
        Determines the generation/storage parameters for the chosen case

    Returns
    -------
    case_list:list
        Simulation order of different scenarios

    """

    case_list = []
    str_cases_simulated = ""
    # Certain ORDER of simulation: First base capacities are optimized
    for case in case_definitions:
        if (
            case_definitions[case][PERFORM_SIMULATION] is True
            and case_definitions[case][BASED_ON_CASE] is False
        ):
            case_list.append(case)
            str_cases_simulated += case + ", "

    logging.info("Base capacities provided by: " + str_cases_simulated[:-2])

    for case in case_definitions:
        if (
            case_definitions[case][PERFORM_SIMULATION] is True
            and case_definitions[case][BASED_ON_CASE] is True
        ):
            case_list.append(case)
            str_cases_simulated += case + ", "

        if len(case_list) == 0:
            logging.error(
                f"No cases defined to be simulated. \n "
                f"Did you set any {PERFORM_SIMULATION}=True in excel template, tab CASE_DEFINITIONS?"
            )
            sys.exit()

    logging.info("All simulated cases: " + str_cases_simulated[:-2])
    return case_list


def economic_values(experiment):
    """
    Introduces the economic values into the experiment dictionary

    Parameters
    ----------
    experiment: dict
        Dictionary containing parameters for sensitivity experiments

    Returns
    -------
    experiment: dict

    """

    """Pre-processing of input data (calculation of economic values)"""
    experiment.update(
        {
            ANNUITY_FACTOR: economics.annuity_factor(
                experiment[PROJECT_LIFETIME], experiment[WACC]
            )
        }
    )
    experiment.update(
        {CRF: economics.crf(experiment[PROJECT_LIFETIME], experiment[WACC])}
    )

    if PRICE_FUEL not in experiment:
        present_value_changing_fuel_price = (
            economics.present_value_of_changing_fuel_price(
                experiment[FUEL_PRICE],
                experiment[PROJECT_LIFETIME],
                experiment[WACC],
                experiment[FUEL_PRICE_CHANGE_ANNUAL],
                experiment[CRF],
            )
        )
        experiment.update({PRICE_FUEL: present_value_changing_fuel_price})
    else:
        logging.warning(
            f"You used decrepated value {PRICE_FUEL} in your excel input file. \n "
            + "    "
            + "    "
            + "    "
            + f"This still works, but with values {FUEL_PRICE} and {FUEL_PRICE_CHANGE_ANNUAL} you could take into account price changes."
        )

    component_list = [
        PV,
        WIND,
        GENSET,
        STORAGE_CAPACITY,
        STORAGE_POWER,
        PCOUPLING,
        MAINGRID_EXTENSION,
        DISTRIBUTION_GRID,
        RECTIFIER_AC_DC,
        INVERTER_DC_AC,
        PROJECT,
    ]

    for item in component_list:
        # --------------------------------------------------#
        # CAPEX without opex/a                              #
        # --------------------------------------------------#
        experiment.update(
            {
                item
                + SUFFIX_COST_CAPEX: economics.capex_from_investment(
                    experiment[item + SUFFIX_COST_INVESTMENT],
                    experiment[item + SUFFIX_LIFETIME],
                    experiment[PROJECT_LIFETIME],
                    experiment[WACC],
                    experiment[TAX],
                )
            }
        )

        # --------------------------------------------------#
        # Annuities of components including opex AND capex #
        # --------------------------------------------------#
        experiment.update(
            {
                item
                + SUFFIX_COST_ANNUITY: economics.annuity(
                    experiment[item + SUFFIX_COST_CAPEX], experiment[CRF]
                )
                + experiment[item + SUFFIX_COST_OPEX]
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
                + SUFFIX_COST_ANNUITY: experiment[item + SUFFIX_COST_ANNUITY]
                / 365
                * experiment[EVALUATED_DAYS]
            }
        )

    return experiment


def add_timeseries(experiment_s):
    """
    Update experiments and add longest date_time_index to settings

    Parameters
    ----------
    experiment_s: dict
        Contains different experiments

    Returns
    -------
    max_date_time_index: pandas.DatetimeIndex
        Datetime from start until end of the experiment

    max_evaluated_days: int
        Number of days evaluated in the experiment
    """

    entries = 0
    longest = ""

    for experiment in experiment_s:
        experiment_s[experiment].update(
            {
                TIME_END: experiment_s[experiment][TIME_START]
                + pd.DateOffset(days=experiment_s[experiment][EVALUATED_DAYS])
                - pd.DateOffset(hours=1)
            }
        )
        # experiment_s[experiment].update({'time_end': experiment_s[experiment]['time_start']+ pd.DateOffset(hours=2)})
        experiment_s[experiment].update(
            {
                DATE_TIME_INDEX: pd.date_range(
                    start=experiment_s[experiment][TIME_START],
                    end=experiment_s[experiment][TIME_END],
                    freq=experiment_s[experiment][TIME_FREQUENCY],
                )
            }
        )

        if len(experiment_s[experiment][DATE_TIME_INDEX]) > entries:
            entries = len(experiment_s[experiment][DATE_TIME_INDEX])
            longest = experiment

    max_date_time_index = experiment_s[longest][DATE_TIME_INDEX]
    max_evaluated_days = experiment_s[longest][EVALUATED_DAYS]

    for experiment in experiment_s:
        index = experiment_s[experiment][DATE_TIME_INDEX]
        if experiment_s[experiment][FILE_INDEX] != None:
            if DEMAND_AC in experiment_s[experiment]:
                year_timeseries_in_file = (
                    experiment_s[experiment][DEMAND_AC].index[0].year
                )
            else:
                year_timeseries_in_file = (
                    experiment_s[experiment][DEMAND_DC].index[0].year
                )

            if (
                experiment_s[experiment][DATE_TIME_INDEX][0].year
                != year_timeseries_in_file
            ):
                file_index = [
                    item + pd.DateOffset(year=index[0].year) for item in index
                ]
                # shift to fileindex of data sets to analysed year
                demand_ac = pd.Series(
                    experiment_s[experiment][DEMAND_AC].values,
                    index=experiment_s[experiment][FILE_INDEX],
                )
                demand_dc = pd.Series(
                    experiment_s[experiment][DEMAND_DC].values,
                    index=experiment_s[experiment][FILE_INDEX],
                )
                pv_generation_per_kWp = pd.Series(
                    experiment_s[experiment][PV_GENERATION_PER_KWP].values,
                    index=experiment_s[experiment][FILE_INDEX],
                )
                wind_generation_per_kW = pd.Series(
                    experiment_s[experiment][WIND_GENERATION_PER_KW].values,
                    index=experiment_s[experiment][FILE_INDEX],
                )
                # from provided data use only analysed timeframe
                experiment_s[experiment].update({DEMAND_PROFILE_AC: demand_ac[index]})
                experiment_s[experiment].update({DEMAND_PROFILE_DC: demand_dc[index]})
                experiment_s[experiment].update(
                    {PV_GENERATION_PER_KWP: pv_generation_per_kWp[index]}
                )
                experiment_s[experiment].update(
                    {WIND_GENERATION_PER_KW: wind_generation_per_kW[index]}
                )

                if GRID_AVAILABILITY in experiment_s[experiment].keys():
                    grid_availability = pd.Series(
                        experiment_s[experiment][GRID_AVAILABILITY].values,
                        index=experiment_s[experiment][FILE_INDEX],
                    )
                    experiment_s[experiment].update(
                        {GRID_AVAILABILITY: grid_availability[index]}
                    )

            else:
                # file index is date time index, no change necessary
                pass

        elif experiment_s[experiment][FILE_INDEX] == None:
            # limit based on index
            experiment_s[experiment].update(
                {
                    DEMAND_PROFILE_AC: pd.Series(
                        experiment_s[experiment][DEMAND_AC][0 : len(index)].values,
                        index=index,
                    )
                }
            )
            experiment_s[experiment].update(
                {
                    DEMAND_PROFILE_DC: pd.Series(
                        experiment_s[experiment][DEMAND_DC][0 : len(index)].values,
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
                    WIND_GENERATION_PER_KW: pd.Series(
                        experiment_s[experiment][WIND_GENERATION_PER_KW][
                            0 : len(index)
                        ].values,
                        index=index,
                    )
                }
            )

            if GRID_AVAILABILITY in experiment_s[experiment].keys():
                experiment_s[experiment].update(
                    {
                        GRID_AVAILABILITY: pd.Series(
                            experiment_s[experiment][GRID_AVAILABILITY][
                                0 : len(index)
                            ].values,
                            index=index,
                        )
                    }
                )

        else:
            logging.warning(
                f"Project site value {FILE_INDEX} neither None not non-None."
            )

        # Used for generation of lp file with only 3-timesteps = Useful to verify optimized equations
        if experiment_s[experiment][LP_FILE_FOR_ONLY_3_TIMESTEPS] is True:
            experiment_s[experiment].update(
                {
                    TIME_START: experiment_s[experiment][TIME_START]
                    + pd.DateOffset(hours=15)
                }
            )
            experiment_s[experiment].update(
                {
                    TIME_END: experiment_s[experiment][TIME_START]
                    + pd.DateOffset(hours=2)
                }
            )
            experiment_s[experiment].update(
                {
                    DATE_TIME_INDEX: pd.date_range(
                        start=experiment_s[experiment][TIME_START],
                        end=experiment_s[experiment][TIME_END],
                        freq=experiment_s[experiment][TIME_FREQUENCY],
                    )
                }
            )

            index = experiment_s[experiment][DATE_TIME_INDEX]
            experiment_s[experiment].update(
                {DEMAND_PROFILE_AC: experiment_s[experiment][DEMAND_PROFILE_AC][index]}
            )
            experiment_s[experiment].update(
                {DEMAND_PROFILE_DC: experiment_s[experiment][DEMAND_PROFILE_DC][index]}
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
                    WIND_GENERATION_PER_KW: experiment_s[experiment][
                        WIND_GENERATION_PER_KW
                    ][index]
                }
            )
            if GRID_AVAILABILITY in experiment_s[experiment].keys():
                experiment_s[experiment].update(
                    {
                        GRID_AVAILABILITY: experiment_s[experiment][GRID_AVAILABILITY][
                            index
                        ]
                    }
                )

        experiment_s[experiment].update(
            {
                ACCUMULATED_PROFILE_AC_SIDE: experiment_s[experiment][DEMAND_PROFILE_AC]
                + experiment_s[experiment][DEMAND_PROFILE_DC]
                / experiment_s[experiment][RECTIFIER_AC_DC_EFFICIENCY]
            }
        )

        experiment_s[experiment].update(
            {
                ACCUMULATED_PROFILE_DC_SIDE: experiment_s[experiment][DEMAND_PROFILE_AC]
                / experiment_s[experiment][INVERTER_DC_AC_EFFICIENCY]
                + experiment_s[experiment][DEMAND_PROFILE_DC]
            }
        )
        experiment_s[experiment].update(
            {
                TOTAL_DEMAND_AC: sum(experiment_s[experiment][DEMAND_PROFILE_AC]),
                PEAK_DEMAND_AC: max(experiment_s[experiment][DEMAND_PROFILE_AC]),
                TOTAL_DEMAND_DC: sum(experiment_s[experiment][DEMAND_PROFILE_DC]),
                PEAK_DEMAND_DC: max(experiment_s[experiment][DEMAND_PROFILE_DC]),
                PEAK_PV_GENERATION_PER_KWP: max(
                    experiment_s[experiment][PV_GENERATION_PER_KWP]
                ),
                PEAK_WIND_GENERATION_PER_KW: max(
                    experiment_s[experiment][WIND_GENERATION_PER_KW]
                ),
            }
        )

        experiment_s[experiment].update(
            {
                MEAN_DEMAND_AC: experiment_s[experiment][TOTAL_DEMAND_AC]
                / len(experiment_s[experiment][DATE_TIME_INDEX]),
                MEAN_DEMAND_DC: experiment_s[experiment][TOTAL_DEMAND_DC]
                / len(experiment_s[experiment][DATE_TIME_INDEX]),
            }
        )

        if experiment_s[experiment][MEAN_DEMAND_AC] > 0:
            experiment_s[experiment].update(
                {
                    PEAK_MEAN_DEMAND_RATIO_AC: experiment_s[experiment][PEAK_DEMAND_AC]
                    / experiment_s[experiment][MEAN_DEMAND_AC]
                }
            )
        else:
            experiment_s[experiment].update({PEAK_MEAN_DEMAND_RATIO_AC: 0})

        if experiment_s[experiment][MEAN_DEMAND_DC] > 0:
            experiment_s[experiment].update(
                {
                    PEAK_MEAN_DEMAND_RATIO_DC: experiment_s[experiment][PEAK_DEMAND_DC]
                    / experiment_s[experiment][MEAN_DEMAND_DC]
                }
            )
        else:
            experiment_s[experiment].update({PEAK_MEAN_DEMAND_RATIO_DC: 0})

        # Used for estimation of capacities using "peak demand"
        experiment_s[experiment].update(
            {
                ABS_PEAK_DEMAND_AC_SIDE: max(
                    experiment_s[experiment][ACCUMULATED_PROFILE_AC_SIDE]
                )
            }
        )

        # Warnings
        if (
            experiment_s[experiment][TOTAL_DEMAND_AC]
            == 0 + experiment_s[experiment][TOTAL_DEMAND_DC]
            == 0
        ):
            logging.warning(
                "No demand in evaluated timesteps at project site "
                + experiment_s[experiment][PROJECT_SITE_NAME]
                + " - simulation will crash."
            )
        if experiment_s[experiment][PEAK_PV_GENERATION_PER_KWP] == 0:
            logging.info(
                "No pv generation in evaluated timesteps at project site "
                + experiment_s[experiment][PROJECT_SITE_NAME]
                + "."
            )
        if experiment_s[experiment][PEAK_WIND_GENERATION_PER_KW] == 0:
            logging.info(
                "No wind generation in evaluated timesteps at project site "
                + experiment_s[experiment][PROJECT_SITE_NAME]
                + "."
            )

    return max_date_time_index, max_evaluated_days


def apply_noise(experiment_s):
    """
    Adds white noise to demands and generations to the timeseries of each experiment.

    #ToDo: Changes are necessary to this function. It may either be not applied currently, or it should be completely deleted.

    Parameters
    ----------
    experiment_s: dict
        Contains different experiments

    Returns
    -------

    """
    for experiment in experiment_s:
        on_series(experiment_s[experiment], WHITE_NOISE_DEMAND, DEMAND_AC)
        on_series(experiment_s[experiment], WHITE_NOISE_DEMAND, DEMAND_DC)
        on_series(experiment_s[experiment], WHITE_NOISE_PV, PV_GENERATION_PER_KWP)
        on_series(experiment_s[experiment], WHITE_NOISE_WIND, WIND_GENERATION_PER_KW)
    return


def on_series(experiment, noise_name, series_name):
    """
    Applies an specific type of noise to an experiment

    Parameters
    ----------
    experiment: dict
        Dictionary containing parameters for sensitivity experiments

    noise_name: str
        Name of the noise to be applied

    series_name:
        Name of the timeseries to be infused with noise

    Returns
    -------
    """
    if experiment[noise_name] != 0:
        series_values = pd.Series(
            randomized(experiment[noise_name], experiment[series_name]),
            index=experiment[series_name].index,
        )
        experiment.update({series_name: series_values})
        # add display of series with noise
    return


def randomized(white_noise_percentage, data_subframe):
    """
    Inserts randomized distribution of noise into the data_subframe

    Parameters
    ----------
    white_noise_percentage: int
        Percentage of white noise to be introduced. Width of the distribution

    data_subframe: pandas.Dataframe
        Dataframe with values to be modified through white noise

    Returns
    -------
    data_subframe: pandas.Dataframe
        Modified version of the subdataframe with white noise included

    """
    import numpy as np

    noise = np.random.normal(0, white_noise_percentage, len(data_subframe))
    for i in range(0, len(data_subframe)):
        if data_subframe[i] != 0:
            data_subframe[i] = data_subframe[i] * (1 - noise[i])
    return data_subframe.clip_lower(0)  # do not allow values <0
