"""
This script creates all possible sensitivity_experiment_s of a sensitivity analysis with a list of sensitive parameters
(bound by min, max, step lenght) and a list of constant parameters. All parameters are stored in a large
dictonary, including filenames.
"""

import pandas as pd
import logging
import os

import itertools
import numpy as np
from copy import deepcopy

# todo: this module should not be called here
import src.D0_process_input as process_input_parameters

from src.constants import (
    BLACKOUT_DURATION,
    BLACKOUT_DURATION_STD_DEVIATION,
    BLACKOUT_FREQUENCY,
    BLACKOUT_FREQUENCY_STD_DEVIATION,
    SENSITIVITY_ALL_COMBINATIONS,
    DEMAND_AC_SCALING_FACTOR,
    DEMAND_DC_SCALING_FACTOR,
    STORAGE_SOC_INITIAL,
    TOTAL_NUMBER_OF_EXPERIMENTS,
    PROJECT_SITE_NAME,
    EXPERIMENT_NAME,
    MIN,
    MAX,
    STEP,
    COMBUSTION_VALUE_FUEL,
    DISTRIBUTION_GRID_COST_INVESTMENT,
    DISTRIBUTION_GRID_COST_OPEX,
    DISTRIBUTION_GRID_LIFETIME,
    GENSET_BATCH,
    GENSET_COST_INVESTMENT,
    GENSET_COST_OPEX,
    GENSET_COST_VAR,
    GENSET_EFFICIENCY,
    GENSET_LIFETIME,
    GENSET_MAX_LOADING,
    GENSET_MIN_LOADING,
    GENSET_OVERSIZE_FACTOR,
    INVERTER_DC_AC_BATCH,
    INVERTER_DC_AC_COST_INVESTMENT,
    INVERTER_DC_AC_COST_OPEX,
    INVERTER_DC_AC_COST_VAR,
    INVERTER_DC_AC_EFFICIENCY,
    INVERTER_DC_AC_LIFETIME,
    MAINGRID_DISTANCE,
    MAINGRID_ELECTRICITY_PRICE,
    MAINGRID_EXTENSION_COST_INVESTMENT,
    MAINGRID_EXTENSION_COST_OPEX,
    MAINGRID_EXTENSION_LIFETIME,
    MAINGRID_FEEDIN_TARIFF,
    MAINGRID_RENEWABLE_SHARE,
    MIN_RENEWABLE_SHARE,
    PCOUPLING_BATCH,
    PCOUPLING_COST_INVESTMENT,
    PCOUPLING_COST_OPEX,
    PCOUPLING_COST_VAR,
    PCOUPLING_EFFICIENCY,
    PCOUPLING_LIFETIME,
    PCOUPLING_OVERSIZE_FACTOR,
    PRICE_FUEL,
    PROJECT_COST_INVESTMENT,
    PROJECT_COST_OPEX,
    PROJECT_LIFETIME,
    PV_BATCH,
    PV_COST_INVESTMENT,
    PV_COST_OPEX,
    PV_COST_VAR,
    PV_LIFETIME,
    RECTIFIER_AC_DC_BATCH,
    RECTIFIER_AC_DC_COST_INVESTMENT,
    RECTIFIER_AC_DC_COST_OPEX,
    RECTIFIER_AC_DC_COST_VAR,
    RECTIFIER_AC_DC_EFFICIENCY,
    RECTIFIER_AC_DC_LIFETIME,
    SHORTAGE_MAX_ALLOWED,
    SHORTAGE_MAX_TIMESTEP,
    SHORTAGE_PENALTY_COST,
    SHORTAGE_LIMIT,
    SHORTAGE_BATCH_CAPACITY,
    SHORTAGE_BATCH_POWER,
    SHORTAGE_CAPACITY_COST_INVESTMENT,
    SHORTAGE_CAPACITY_COST_OPEX,
    STORAGE_CAPACITY_LIFETIME,
    STORAGE_COST_VAR,
    STORAGE_CRATE_CHARGE,
    STORAGE_CRATE_DISCHARGE,
    STORAGE_EFFICIENCY_CHARGE,
    STORAGE_EFFICIENCY_DISCHARGE,
    STORAGE_LOSS_TIMESTEP,
    STORAGE_POWER_COST_INVESTMENT,
    STORAGE_POWER_COST_OPEX,
    STORAGE_POWER_LIFETIME,
    STORAGE_SOC_MAX,
    STORAGE_SOC_MIN,
    TAX,
    WACC,
    WHITE_NOISE_DEMAND,
    WHITE_NOISE_PV,
    WHITE_NOISE_WIND,
    WIND_BATCH,
    WIND_COST_INVESTMENT,
    WIND_COST_OPEX,
    WIND_COST_VAR,
    WIND_LIFETIME,
    FUEL_PRICE,
    FUEL_PRICE_CHANGE_ANNUAL,
    CASE,
    RESULTS_DEMAND_CHARACTERISTICS,
    RESULTS_BLACKOUT_CHARACTERISTICS,
    CAPACITY_INVERTER_KW,
    LCOE,
    ANNUITY,
    NPV,
    SUPPLY_RELIABILITY_KWH,
    RES_SHARE,
    AUTONOMY_FACTOR,
    TOTAL_DEMAND_ANNUAL_KWH,
    DEMAND_PEAK_KW,
    TOTAL_DEMAND_SUPPLIED_ANNUAL_KWH,
    TOTAL_DEMAND_SHORTAGE_ANNUAL_KWH,
    NATIONAL_GRID_RELIABILITY_H,
    NATIONAL_GRID_TOTAL_BLACKOUT_DURATION,
    NATIONAL_GRID_NUMBER_OF_BLACKOUTS,
    TOTAL_PV_GENERATION_KWH,
    TOTAL_WIND_GENERATION_KWH,
    TOTAL_GENSET_GENERATION_KWH,
    CONSUMPTION_FUEL_ANNUAL_L,
    GENSET_HOURS_OF_OPERATION,
    CONSUMPTION_MAIN_GRID_MG_SIDE_ANNUAL_KWH,
    FEEDIN_MAIN_GRID_MG_SIDE_ANNUAL_KWH,
    RESULTS_ANNUITIES,
    ANNUITY_PV,
    ANNUITY_STORAGE,
    ANNUITY_RECTIFIER_AC_DC,
    ANNUITY_INVERTER_DC_AC,
    ANNUITY_WIND,
    ANNUITY_GENSET,
    ANNUITY_PCOUPLING,
    ANNUITY_DISTRIBUTION_GRID,
    ANNUITY_PROJECT,
    ANNUITY_MAINGRID_EXTENSION,
    EXPENDITURES_FUEL_ANNUAL,
    EXPENDITURES_MAIN_GRID_CONSUMPTION_ANNUAL,
    EXPENDITURES_SHORTAGE_ANNUAL,
    REVENUE_MAIN_GRID_FEEDIN_ANNUAL,
    RESULTS_COSTS,
    COSTS_PV,
    COSTS_STORAGE,
    COSTS_RECTIFIER_AC_DC,
    COSTS_INVERTER_DC_AC,
    COSTS_WIND,
    COSTS_GENSET,
    COSTS_PCOUPLING,
    COSTS_DISTRIBUTION_GRID,
    COSTS_PROJECT,
    FIRST_INVESTMENT,
    OPERATION_MAINTAINANCE_EXPENDITURES,
    COSTS_MAINGRID_EXTENSION,
    EXPENDITURES_FUEL_TOTAL,
    EXPENDITURES_MAIN_GRID_CONSUMPTION_TOTAL,
    EXPENDITURES_SHORTAGE_TOTAL,
    REVENUE_MAIN_GRID_FEEDIN_TOTAL,
    OBJECTIVE_VALUE,
    SIMULATION_TIME,
    EVALUATION_TIME,
    FILENAME,
    COMMENTS,
    CAPACITY_PCOUPLING_KW,
    DEMAND_AC,
    DEMAND_DC,
    PV_GENERATION_PER_KWP,
    WIND_GENERATION_PER_KW,
    GRID_AVAILABILITY,
    OUTPUT_FOLDER,
    CAPACITY_PV_KWP,
    CAPACITY_STORAGE_KWH,
    POWER_STORAGE_KW,
    CAPACITY_RECTIFIER_AC_DC_KW,
    CAPACITY_WIND_KW,
    CAPACITY_GENSET_KW,
    CO2_EMISSIONS_KGC02EQ,
    TOTAL_EXCESS_ANNUAL_KWH,
    CONSUMPTION_FUEL_ANNUAL_KWH,
    SENSITIVITY_EXPERIMENTS_CSV,
    SIMULATION_EXPERIMENTS_CSV,
)


def get_blackout_experiment_name(blackout_experiment):
    """
    Generate names for blackout sensitivity_experiment_s, used in sensitivity.blackout experiments and in maintool

    Parameters
    ----------
    blackout_experiment: dict
        Settings for the blackout experiment

    Returns
    -------
    blackout_experiment_name: str
        Name of the experiment containing its settings

    """

    blackout_experiment_name = (
        "blackout_dur"
        + "_"
        + str(round(float(blackout_experiment[BLACKOUT_DURATION]), 3))
        + "_"
        + "dur_dev"
        + "_"
        + str(round(float(blackout_experiment[BLACKOUT_DURATION_STD_DEVIATION]), 3))
        + "_"
        + "freq"
        + "_"
        + str(round(float(blackout_experiment[BLACKOUT_FREQUENCY]), 3))
        + "_"
        + "freq_dev"
        + "_"
        + str(round(float(blackout_experiment[BLACKOUT_FREQUENCY_STD_DEVIATION]), 3))
    )
    return blackout_experiment_name


# Sensitivy
def get(settings, parameters_constant_values, parameters_sensitivity, project_sites):
    """
    Get sensitivity_experiment_s for sensitivity analysis

    Parameters
    ----------
    settings: dict
        Contains experiment's settings

    parameters_constant_values: dict
        Contains constant parameters

    parameters_sensitivity: dict
        Sensitivity range for the chosen element {Elem: Min, Max, Step}

    project_sites: dict
        Contains information of the projects sites timeseries

    Returns
    -------
    sensitivitiy_experiment_s: dict
        Settings for the different sensitivity experiments

    blackout_experiment_s: dict
        Settings for the blackout experiments

    title_overall_results: pandas.Dataframe
        Empty dataframe to be filled with results

    names_sensitivities: list
        Contains parameters to be analyzed in the sensitivity experiment

    """

    if settings[SENSITIVITY_ALL_COMBINATIONS] is True:
        (
            sensitivitiy_experiment_s,
            number_of_project_sites,
            sensitivity_array_dict,
            total_number_of_experiments,
        ) = all_possible(
            settings, parameters_constant_values, parameters_sensitivity, project_sites,
        )

    elif settings[SENSITIVITY_ALL_COMBINATIONS] is False:
        (
            sensitivitiy_experiment_s,
            number_of_project_sites,
            sensitivity_array_dict,
            total_number_of_experiments,
        ) = with_base_case(
            settings, parameters_constant_values, parameters_sensitivity, project_sites,
        )

    else:
        logging.warning(
            "Setting SENSITIVITY_ALL_COMBINATIONS not valid! Has to be TRUE or FALSE."
        )

    names_sensitivities = [key for key in sensitivity_array_dict.keys()]

    message = "Parameters of sensitivity analysis: "
    for entry in names_sensitivities:
        message += entry + ", "

    logging.info(message[:-2])

    for experiment in sensitivitiy_experiment_s:
        test_techno_economical_parameters_complete(
            sensitivitiy_experiment_s[experiment]
        )

        # scaling demand according to scaling factor - used for tests regarding tool application
        sensitivitiy_experiment_s[experiment].update(
            {
                DEMAND_AC: sensitivitiy_experiment_s[experiment][DEMAND_AC]
                * sensitivitiy_experiment_s[experiment][DEMAND_AC_SCALING_FACTOR]
            }
        )
        sensitivitiy_experiment_s[experiment].update(
            {
                DEMAND_DC: sensitivitiy_experiment_s[experiment][DEMAND_DC]
                * sensitivitiy_experiment_s[experiment][DEMAND_DC_SCALING_FACTOR]
            }
        )

        #  Add economic values to sensitivity sensitivity_experiment_s
        process_input_parameters.economic_values(sensitivitiy_experiment_s[experiment])
        # Give a file item to the sensitivity_experiment_s
        experiment_name(
            sensitivitiy_experiment_s[experiment],
            sensitivity_array_dict,
            number_of_project_sites,
        )

        if COMMENTS not in sensitivitiy_experiment_s[experiment]:
            sensitivitiy_experiment_s[experiment].update({COMMENTS: ""})

        if sensitivitiy_experiment_s[experiment][STORAGE_SOC_INITIAL] == "None":
            sensitivitiy_experiment_s[experiment].update({STORAGE_SOC_INITIAL: None})
    #######################################################
    # Get blackout_experiment_s for sensitvitiy           #
    #######################################################
    # Creating dict of possible blackout scenarios (combinations of durations  frequencies
    (blackout_experiment_s, blackout_experiments_count,) = blackout(
        sensitivity_array_dict, parameters_constant_values, settings
    )

    # save all Experiments with all used input data to csv
    csv_dict = deepcopy(sensitivitiy_experiment_s)
    # delete timeseries to make file readable
    timeseries_names = [
        DEMAND_AC,
        DEMAND_DC,
        PV_GENERATION_PER_KWP,
        WIND_GENERATION_PER_KW,
        GRID_AVAILABILITY,
    ]
    for entry in csv_dict:
        for series in timeseries_names:
            if series in csv_dict[entry].keys():
                del csv_dict[entry][series]

    experiments_dataframe = pd.DataFrame.from_dict(csv_dict, orient="index")
    experiments_dataframe.to_csv(
        os.path.join(settings[OUTPUT_FOLDER], SIMULATION_EXPERIMENTS_CSV)
    )

    for item in experiments_dataframe.columns:
        if (item not in parameters_sensitivity.keys()) and (
            item not in [PROJECT_SITE_NAME]
        ):
            experiments_dataframe = experiments_dataframe.drop(columns=item)

    experiments_dataframe.to_csv(
        os.path.join(settings[OUTPUT_FOLDER], SENSITIVITY_EXPERIMENTS_CSV)
    )

    # Generate a overall title of the oemof-results DataFrame
    title_overall_results = overall_results_title(
        settings, number_of_project_sites, sensitivity_array_dict
    )

    message = "For " + str(number_of_project_sites) + " project sites"
    message += (
        " with "
        + str(int(total_number_of_experiments / number_of_project_sites))
        + " scenarios each,"
    )
    message += (
        " "
        + str(total_number_of_experiments)
        + " sensitivity_experiment_s will be performed for each case."
    )

    logging.info(message)

    settings.update({TOTAL_NUMBER_OF_EXPERIMENTS: total_number_of_experiments})

    return (
        sensitivitiy_experiment_s,
        blackout_experiment_s,
        title_overall_results,
        names_sensitivities,
    )


# Generate Exp
def all_possible(
    settings, parameters_constant_values, parameters_sensitivity, project_site_s
):
    """
    Generates cases for all sensitivity experiments

    Parameters
    ----------
    settings: dict
        Contains experiment's settings

    parameters_constant_values: dict
        Contains constant parameters

    parameters_sensitivity: dict
        Sensitivity range for the chosen element {Elem : Min, Max, Step}

    project_site_s: dict
        Parameter values for the projects_site (Inlcuding time-series demand)

    Returns
    -------
    sensitivity_experiment_s: dict
        Settings for different sensitivity experiments

    number_of_project_sites: int

    sensitivity_array_dict: dict
        Contains element for SE and values for the corresponding sensitivities

    total_number_of_experiments: int

    """

    # Deletes constants from parameters_constant_values depending on values defined in sensitivity
    constants_senstivity(parameters_constant_values, parameters_sensitivity)
    # Deletes constants from parameters_constant_values depending on values defined in project sites
    constants_project_sites(parameters_constant_values, project_site_s)
    # Deletes project site parameter that is also included in sensitivity analysis
    project_sites_sensitivity(parameters_sensitivity, project_site_s)

    # From now on, universal parameters poses the base scenario. some parameters might only be set with project sites!
    universal_parameters, number_of_project_sites = get_universal_parameters(
        settings, parameters_constant_values, parameters_sensitivity, project_site_s
    )

    sensitivity_array_dict = get_dict_sensitivies_arrays(
        parameters_sensitivity, project_site_s
    )

    project_site_dict = {PROJECT_SITE_NAME: [key for key in project_site_s.keys()]}
    (
        sensitivity_experiment_s,
        total_number_of_experiments,
    ) = get_all_possible_combinations(sensitivity_array_dict, project_site_dict)

    for experiment in sensitivity_experiment_s:
        sensitivity_experiment_s[experiment].update(deepcopy(universal_parameters))
        sensitivity_experiment_s[experiment].update(
            deepcopy(
                project_site_s[sensitivity_experiment_s[experiment][PROJECT_SITE_NAME]]
            )
        )

    return (
        sensitivity_experiment_s,
        number_of_project_sites,
        sensitivity_array_dict,
        total_number_of_experiments,
    )


def with_base_case(
    settings, parameters_constant_values, parameters_sensitivity, project_site_s
):
    """
    Generates sensitivity experiment around the base case

    Parameters
    ----------
    settings: dict
        Contains experiment's settings

    parameters_constant_values: dict
        Contains constant parameters

    parameters_sensitivity: dict
        Sensitivity range for the chosen element {Elem : Min, Max, Step}

    project_site_s: dict
        Parameter values for the projects_site (Inlcuding time-series demand)

    Returns
    -------
    sensitivity_experiment_s: dict
        Settings for different sensitivity experiments

    number_of_project_sites: int

    sensitivity_array_dict: dict
        Contains element for SE and values for the corresponding sensitivities

    total_number_of_experiments: int
    """
    constants_project_sites(parameters_constant_values, project_site_s)

    universal_parameters, number_of_project_sites = get_universal_parameters(
        settings, parameters_constant_values, parameters_sensitivity, project_site_s
    )

    # From now on, universal parameters poses the base scenario. some parameters might only be set with project sites!
    sensitivity_array_dict = get_dict_sensitivies_arrays(
        parameters_sensitivity, project_site_s
    )

    (
        sensitivity_experiment_s,
        total_number_of_experiments,
    ) = get_combinations_around_base(
        sensitivity_array_dict, universal_parameters, project_site_s
    )

    return (
        sensitivity_experiment_s,
        number_of_project_sites,
        sensitivity_array_dict,
        total_number_of_experiments,
    )


def blackout(sensitivity_array_dict, parameters_constants, settings):
    """
    Creates blackout experiments with parameters contained in the array

    Parameters
    ----------
    sensitivity_array_dict: dict
        Contains element for SE and values for the corresponding sensitivities

    parameters_constants: dict
        Setting for blackout experiment

    settings: dict
            General settings for the simulation


    Returns
    -------
    blackout_experiment_s:
        Settings for all blackout experiments

    blackout_experiments_count: int
    """

    blackout_parameters = deepcopy(sensitivity_array_dict)
    for parameter in sensitivity_array_dict:
        if (
            parameter != BLACKOUT_DURATION
            and parameter != BLACKOUT_FREQUENCY
            and parameter != BLACKOUT_DURATION_STD_DEVIATION
            and parameter != BLACKOUT_FREQUENCY_STD_DEVIATION
        ):
            del blackout_parameters[parameter]

    blackout_constants = deepcopy(parameters_constants)
    for parameter in parameters_constants:
        if (
            parameter != BLACKOUT_DURATION
            and parameter != BLACKOUT_FREQUENCY
            and parameter != BLACKOUT_DURATION_STD_DEVIATION
            and parameter != BLACKOUT_FREQUENCY_STD_DEVIATION
            and parameter not in sensitivity_array_dict
        ):
            del blackout_constants[parameter]

    if settings[SENSITIVITY_ALL_COMBINATIONS] is True:
        (
            blackout_experiment_s,
            blackout_experiments_count,
        ) = get_all_possible_combinations(blackout_parameters, {})
        for blackout_experiment in blackout_experiment_s:
            blackout_experiment_s[blackout_experiment].update(
                deepcopy(blackout_constants)
            )

    elif settings[SENSITIVITY_ALL_COMBINATIONS] is False:
        blackout_experiment_s = {}
        blackout_experiments_count = 0
        defined_base = False

        for key in blackout_parameters:
            for interval_entry in range(0, len(sensitivity_array_dict[key])):
                if key in blackout_constants:
                    key_value = blackout_constants[key]
                else:
                    # if not defined in project sites or universal values, use sensitivity value
                    key_value = None

                if sensitivity_array_dict[key][interval_entry] != key_value:
                    # All parameters like base case except for sensitivity parameter
                    blackout_experiments_count += 1
                    blackout_experiment_s.update(
                        {blackout_experiments_count: deepcopy(blackout_constants)}
                    )
                    blackout_experiment_s[blackout_experiments_count].update(
                        {key: sensitivity_array_dict[key][interval_entry]}
                    )
                elif (
                    sensitivity_array_dict[key][interval_entry] == key_value
                    and defined_base is False
                ):
                    # Defining scenario only with base case values for universal parameter / specific to project site (once!)
                    blackout_experiments_count += 1
                    blackout_experiment_s.update(
                        {blackout_experiments_count: deepcopy(blackout_constants)}
                    )
                    blackout_experiment_s[blackout_experiments_count].update(
                        {key: key_value}
                    )
                    defined_base is True

        if len(blackout_experiment_s) == 0:
            blackout_experiments_count += 1
            blackout_experiment_s.update(
                {blackout_experiments_count: deepcopy(blackout_constants)}
            )

    else:
        logging.warning(
            "Setting SENSITIVITY_ALL_COMBINATIONS not valid! Has to be TRUE or FALSE."
        )

    # define file item to save simulation / get grid availabilities
    for blackout_experiment in blackout_experiment_s:
        blackout_experiment_name = get_blackout_experiment_name(
            blackout_experiment_s[blackout_experiment]
        )
        blackout_experiment_s[blackout_experiment].update(
            {EXPERIMENT_NAME: blackout_experiment_name}
        )

    # delete all doubled entries -> could also be applied to experiments!
    experiment_copy = deepcopy(blackout_experiment_s)

    for i in experiment_copy:
        for e in experiment_copy:

            if (
                i != e
                and experiment_copy[i][EXPERIMENT_NAME]
                == experiment_copy[e][EXPERIMENT_NAME]
            ):
                if i in blackout_experiment_s and e in blackout_experiment_s:
                    del blackout_experiment_s[e]

    logging.info(
        "Randomized blackout timeseries for all combinations of blackout duration and frequency ("
        + str(len(blackout_experiment_s))
        + " experiments) will be generated."
    )

    return blackout_experiment_s, blackout_experiments_count


def get_universal_parameters(
    settings, parameters_constant_values, parameters_sensitivity, project_site_s
):
    """
    Creates the base case by copying the settings and the constant values

    Parameters
    ----------
    settings: dict
            General settings for the simulation

    parameters_constant_values: dict
        Contains constant parameters

    parameters_sensitivity: dict
        Sensitivity range for the chosen element {Elem : Min, Max, Step}

    project_site_s: dict
        Parameter values for the projects_site (Inlcuding time-series demand)

    Returns
    -------
    universal_parameters: dict
        Global settings for the simulation

    number_of_project_sites: int
    """

    # create base case
    universal_parameters = deepcopy(settings)
    universal_parameters.update(deepcopy(parameters_constant_values))

    number_of_project_sites = 0
    for key in project_site_s:
        number_of_project_sites += 1

    return universal_parameters, number_of_project_sites


def get_dict_sensitivies_arrays(parameters_sensitivity, project_sites):
    """
    Creates a dict containing elements and values for sensitivity experiments

    Parameters
    ----------
    parameters_sensitivity: dict
        Sensitivity range for the chosen element {Elem : Min, Max, Step}

    project_sites: dict
        Contains information of the projects sites timeseries

    Returns
    -------
    sensitivity_array_dict: dict
        Contains element for SE and values for the corresponding sensitivities

    """
    # fill dictionary with all sensitivity ranges defining the different simulations of the sensitivity analysis
    # ! do not use a key two times, as it will be overwritten by new information
    sensitivity_array_dict = {}
    for keys in parameters_sensitivity:
        if parameters_sensitivity[keys][MIN] == parameters_sensitivity[keys][MAX]:
            sensitivity_array_dict.update(
                {keys: np.array([parameters_sensitivity[keys][MIN]])}
            )
        else:
            sensitivity_array_dict.update(
                {
                    keys: np.arange(
                        parameters_sensitivity[keys][MIN],
                        parameters_sensitivity[keys][MAX]
                        + parameters_sensitivity[keys][STEP] / 2,
                        parameters_sensitivity[keys][STEP],
                    )
                }
            )
    return sensitivity_array_dict


def get_all_possible_combinations(sensitivity_array_dict, name_entry_dict):
    """
    Creates all possible sensitivity experiences based on the elements and values in the array

    Parameters
    ----------
    sensitivity_array_dict: dict
        Contains element for SE and values for the corresponding sensitivities

    name_entry_dict: dict
        Name of the projects site(s)

    Returns
    -------
    sensitivity_experiment_s: dict
        Settings for different sensitivity experiments

    total_number_of_experiments: int

    """
    # create all possible combinations of sensitive parameters
    all_parameters = {}
    for key in sensitivity_array_dict:
        all_parameters.update({key: [value for value in sensitivity_array_dict[key]]})

    all_parameters.update(deepcopy(name_entry_dict))
    # create all possible combinations of sensitive parameters
    keys = [key for key in all_parameters.keys()]
    values = [all_parameters[key] for key in all_parameters.keys()]
    all_experiments = [dict(zip(keys, v)) for v in itertools.product(*values)]

    number_of_experiment = 0
    sensitivity_experiment_s = {}
    for experiment in all_experiments:
        number_of_experiment += 1
        sensitivity_experiment_s.update({number_of_experiment: deepcopy(experiment)})

    total_number_of_experiments = number_of_experiment

    return sensitivity_experiment_s, total_number_of_experiments


def get_combinations_around_base(
    sensitivity_array_dict, universal_parameters, project_site_s
):
    """
    Create sensitivity experiments based on the base case in universal parameters

    Parameters
    ----------
    sensitivity_array_dict: dict
        Contains element for SE and values for the corresponding sensitivities

    universal_parameters: dict
        Global settings for the simulation

    project_site_s: dict
        Parameter values for the projects_site (Inlcuding time-series demand)

    Returns
    -------
    sensitivity_experiment_s: dict
        Settings for different sensitivity experiments

    total_number_of_experiments: int
    """

    experiment_number = 0
    sensitivity_experiment_s = {}

    for project_site in project_site_s:
        # if no sensitivity analysis performed (other than multiple locations)
        if len(sensitivity_array_dict.keys()) == 0:
            experiment_number += 1
            sensitivity_experiment_s.update(
                {experiment_number: deepcopy(universal_parameters)}
            )
            sensitivity_experiment_s[experiment_number].update(
                {PROJECT_SITE_NAME: project_site}
            )
            sensitivity_experiment_s[experiment_number].update(
                deepcopy(project_site_s[project_site])
            )
        # generate cases with sensitivity parameters
        else:
            defined_base = False

            for key in sensitivity_array_dict:
                for interval_entry in range(0, len(sensitivity_array_dict[key])):
                    if key in project_site_s[project_site]:
                        # if defined in project sites, use this value as base case value
                        key_value = project_site_s[project_site][key]
                    elif key in universal_parameters:
                        # if not defined in project sites, use this value as base case value
                        key_value = universal_parameters[key]
                    else:
                        # if not defined in project sites or universal values, use sensitivity value
                        key_value = None

                    if sensitivity_array_dict[key][interval_entry] != key_value:
                        # All parameters like base case except for sensitivity parameter
                        experiment_number += 1
                        sensitivity_experiment_s.update(
                            {experiment_number: deepcopy(universal_parameters)}
                        )
                        sensitivity_experiment_s[experiment_number].update(
                            {PROJECT_SITE_NAME: project_site}
                        )
                        sensitivity_experiment_s[experiment_number].update(
                            deepcopy(project_site_s[project_site])
                        )
                        # overwrite base case value by sensitivity value (only in case specific parameter is changed)
                        sensitivity_experiment_s[experiment_number].update(
                            {key: sensitivity_array_dict[key][interval_entry]}
                        )

                    elif (
                        sensitivity_array_dict[key][interval_entry] == key_value
                        and defined_base is False
                    ):
                        # Defining scenario only with base case values for universal parameter / specific to project site (once!)
                        experiment_number += 1
                        sensitivity_experiment_s.update(
                            {experiment_number: deepcopy(universal_parameters)}
                        )
                        sensitivity_experiment_s[experiment_number].update(
                            {key: key_value}
                        )
                        sensitivity_experiment_s[experiment_number].update(
                            {PROJECT_SITE_NAME: project_site}
                        )
                        sensitivity_experiment_s[experiment_number].update(
                            deepcopy(project_site_s[project_site])
                        )
                        defined_base = True
                        sensitivity_experiment_s[experiment_number].update(
                            {COMMENTS: "Base case, "}
                        )

    total_number_of_experiments = experiment_number
    return sensitivity_experiment_s, total_number_of_experiments


def project_site_experiments(sensitivity_experiment_s, project_sites):
    """
    Creates dict containing the sensitivity experiments from the project_sites dict

    Parameters
    ----------
    sensitivity_experiment_s: dict
        Settings for different sensitivity experiments

    project_sites: dict
        Contains information of the projects sites timeseries

    Returns
    -------
    experiment_s: dict
        Result of the experiment in diferent sites (?)

    number_of_experiments:int
    """
    experiment_s = {}
    number_of_experiments = 0
    for experiment in sensitivity_experiment_s:
        # fill dictionary with all constant values defining the different simulations of the sensitivity analysis
        # ! do not use a key two times or in sensitivity_bounds as well, as it will be overwritten by new information
        number_of_experiments += 1
        experiment_s.update(
            {number_of_experiments: deepcopy(sensitivity_experiment_s[experiment])}
        )
        experiment_s[number_of_experiments].update(
            deepcopy(project_sites[experiment_s[experiment][PROJECT_SITE_NAME]])
        )

    return experiment_s, number_of_experiments


def experiment_name(experiment, sensitivity_array_dict, number_of_project_sites):
    """
    Generates names for all experiments

    Parameters
    ----------
    experiment: dict
        Contains all details of the simulation experiment

    sensitivity_array_dict: dict
        Contains element for SE and values for the corresponding sensitivities

    number_of_project_sites: int

    Returns
    --------
    """
    # define file postfix to save simulation
    filename = "_s"
    if number_of_project_sites > 1:
        if isinstance(experiment[PROJECT_SITE_NAME], str):
            filename = filename + "_" + experiment[PROJECT_SITE_NAME]
        else:
            filename = filename + "_" + str(experiment[PROJECT_SITE_NAME])
    else:
        filename = filename

    # this generates alphabetically sorted file/experiment titles
    # ensuring that simulations can be restarted and old results are recognized
    sensitivity_titles = (
        pd.DataFrame.from_dict(sensitivity_array_dict, orient="index")
        .sort_index()
        .index
    )
    # generating all names
    for keys in sensitivity_titles:
        if isinstance(experiment[keys], str):
            filename = filename + "_" + keys + "_" + experiment[keys]
        else:
            filename = (
                filename + "_" + keys + "_" + str(round(float(experiment[keys]), 3))
            )
    # is no sensitivity analysis performed, do not add filename
    if filename == "_s":
        filename = ""
    experiment.update({FILENAME: filename})
    return


def constants_project_sites(parameters_constant_values, project_sites):
    """
    Remove all entries that are doubled in parameters_constant_values, settings & project_site_s from parameters_constant_values

    Parameters
    ----------
    parameters_constant_values: dict
        Contains constant parameters

    project_sites: dict
        Contains information of the projects sites timeseries

    Returns
    -------
    """

    str = 'Attributes "'
    keys = deepcopy(parameters_constant_values).keys()
    for key in keys:
        count = 0
        for location in project_sites.keys():
            if key in project_sites[location].keys():
                if count == 0:
                    del parameters_constant_values[key]
                    str += key + ", "
                count += 1
    if str != 'Attributes "':
        str = (
            str[:-2]
            + '" defined in constant and project site parameters. Only project site value will be used for sensitivity_experiment_s.'
        )
        logging.warning(str)
    return


def project_sites_sensitivity(parameters_sensitivity, project_sites):
    """
    Remove all entries that are doubled in sensitivity_bounds/project_site_s from project site

    Parameters
    ----------
    parameters_sensitivity: dict
        Sensitivity range for the chosen element {Elem : Min, Max, Step}

    project_sites: dict
        Contains information of the projects sites timeseries

    Returns
    --------
    """

    str = 'Attributes "'
    keys = deepcopy(parameters_sensitivity).keys()
    for key in keys:
        count = 0
        for location in project_sites.keys():
            if key in project_sites[location].keys():
                del project_sites[location][key]
                if count == 0:
                    str += key + ", "
                count += 1

    if str != 'Attributes "':
        str = (
            str[:-2]
            + '" defined in project site and sensitvity parameters. Only sensitivity parameters will be used for sensitivity_experiment_s.'
        )
        logging.warning(str)

    return


def constants_senstivity(parameters_constant_values, parameters_sensitivity):
    """
    Remove all entries that are doubled in parameters_constant_values, settings & parameters_sensitivity

    Parameters
    ----------
    parameters_constant_values: dict
        Contains constant parameters

    parameters_sensitivity: dict
        Sensitivity range for the chosen element {Elem : Min, Max, Step}

    Returns
    -------
    """

    str = 'Attributes "'
    keys = deepcopy(parameters_constant_values).keys()
    for key in keys:
        if key in parameters_sensitivity:
            del parameters_constant_values[key]
            str += key + ", "
    if str != 'Attributes "':
        str = (
            str[:-2]
            + '" defined in constant and sensitivity parameters. Only sensitivity parameter value will be used for sensitivity_experiment_s.'
        )
        logging.warning(str)
    return


def test_techno_economical_parameters_complete(experiment):
    """
    Verifies the validity of the experiment's settings

    Parameters
    ----------
    experiment: dict
        Contains all details of the simulation experiment

    Returns
    -------

    """
    parameter_list = {
        BLACKOUT_DURATION: 0,
        BLACKOUT_DURATION_STD_DEVIATION: 0,
        BLACKOUT_FREQUENCY: 0,
        BLACKOUT_FREQUENCY_STD_DEVIATION: 0,
        COMBUSTION_VALUE_FUEL: 9.8,
        DEMAND_AC_SCALING_FACTOR: 1,
        DEMAND_DC_SCALING_FACTOR: 1,
        DISTRIBUTION_GRID_COST_INVESTMENT: 0,
        DISTRIBUTION_GRID_COST_OPEX: 0,
        DISTRIBUTION_GRID_LIFETIME: 0,
        #'fuel_price': 0.76,
        #'fuel_price_change_annual': 0,
        GENSET_BATCH: 1,
        GENSET_COST_INVESTMENT: 0,
        GENSET_COST_OPEX: 0,
        GENSET_COST_VAR: 0,
        GENSET_EFFICIENCY: 0.33,
        GENSET_LIFETIME: 15,
        GENSET_MAX_LOADING: 1,
        GENSET_MIN_LOADING: 0,
        GENSET_OVERSIZE_FACTOR: 1.2,
        INVERTER_DC_AC_BATCH: 1,
        INVERTER_DC_AC_COST_INVESTMENT: 0,
        INVERTER_DC_AC_COST_OPEX: 0,
        INVERTER_DC_AC_COST_VAR: 0,
        INVERTER_DC_AC_EFFICIENCY: 1,
        INVERTER_DC_AC_LIFETIME: 15,
        MAINGRID_DISTANCE: 0,
        MAINGRID_ELECTRICITY_PRICE: 0.15,
        MAINGRID_EXTENSION_COST_INVESTMENT: 0,
        MAINGRID_EXTENSION_COST_OPEX: 0,
        MAINGRID_EXTENSION_LIFETIME: 40,
        MAINGRID_FEEDIN_TARIFF: 0,
        MAINGRID_RENEWABLE_SHARE: 0,
        MIN_RENEWABLE_SHARE: 0,
        PCOUPLING_BATCH: 1,
        PCOUPLING_COST_INVESTMENT: 0,
        PCOUPLING_COST_OPEX: 0,
        PCOUPLING_COST_VAR: 0,
        PCOUPLING_EFFICIENCY: 1,
        PCOUPLING_LIFETIME: 15,
        PCOUPLING_OVERSIZE_FACTOR: 1.05,
        PRICE_FUEL: 0.76,
        PROJECT_COST_INVESTMENT: 0,
        PROJECT_COST_OPEX: 0,
        PROJECT_LIFETIME: 20,
        PV_BATCH: 1,
        PV_COST_INVESTMENT: 0,
        PV_COST_OPEX: 0,
        PV_COST_VAR: 0,
        PV_LIFETIME: 20,
        RECTIFIER_AC_DC_BATCH: 1,
        RECTIFIER_AC_DC_COST_INVESTMENT: 0,
        RECTIFIER_AC_DC_COST_OPEX: 0,
        RECTIFIER_AC_DC_COST_VAR: 0,
        RECTIFIER_AC_DC_EFFICIENCY: 1,
        RECTIFIER_AC_DC_LIFETIME: 15,
        SHORTAGE_MAX_ALLOWED: 0,
        SHORTAGE_MAX_TIMESTEP: 1,
        SHORTAGE_PENALTY_COST: 0.2,
        SHORTAGE_LIMIT: 0.4,
        SHORTAGE_BATCH_CAPACITY: 1,
        SHORTAGE_BATCH_POWER: 1,
        SHORTAGE_CAPACITY_COST_INVESTMENT: 0,
        SHORTAGE_CAPACITY_COST_OPEX: 0,
        STORAGE_CAPACITY_LIFETIME: 5,
        STORAGE_COST_VAR: 0,
        STORAGE_CRATE_CHARGE: 1,
        STORAGE_CRATE_DISCHARGE: 1,
        STORAGE_EFFICIENCY_CHARGE: 0.8,
        STORAGE_EFFICIENCY_DISCHARGE: 1,
        STORAGE_LOSS_TIMESTEP: 0,
        STORAGE_POWER_COST_INVESTMENT: 0,
        STORAGE_POWER_COST_OPEX: 0,
        STORAGE_POWER_LIFETIME: 5,
        STORAGE_SOC_INITIAL: None,
        STORAGE_SOC_MAX: 0.95,
        STORAGE_SOC_MIN: 0.3,
        TAX: 0,
        WACC: 0.09,
        WHITE_NOISE_DEMAND: 0,
        WHITE_NOISE_PV: 0,
        WHITE_NOISE_WIND: 0,
        WIND_BATCH: 1,
        WIND_COST_INVESTMENT: 0,
        WIND_COST_OPEX: 0,
        WIND_COST_VAR: 0,
        WIND_LIFETIME: 15,
    }

    for parameter in parameter_list:
        if parameter not in experiment:
            if (
                (parameter == PRICE_FUEL)
                and (FUEL_PRICE in experiment)
                and (FUEL_PRICE_CHANGE_ANNUAL in experiment)
            ):
                pass
            else:
                logging.warning(
                    'Parameter "'
                    + parameter
                    + '" missing. Do you use an old excel-template? \n'
                    + "    "
                    + "    "
                    + "    "
                    + 'Simulation will continue with generic value of "'
                    + parameter
                    + '": '
                    + str(parameter_list[parameter])
                )

                experiment.update({parameter: parameter_list[parameter]})


def overall_results_title(settings, number_of_project_sites, sensitivity_array_dict):
    """
    Creates Dataframe containinig all general information about the simulations results

    Parameters
    ----------
    settings: dict
            General settings for the simulation

    number_of_project_sites: int

    sensitivity_array_dict: dict
        Contains element for SE and values for the corresponding sensitivities


    Returns
    -------
    title_overall_results: pandas.DataFrame
        Contains the values for every analyzed parameter
    """
    logging.debug("Generating header for results.csv")
    title_overall_results = pd.DataFrame(columns=[CASE, PROJECT_SITE_NAME])

    for keys in sensitivity_array_dict:
        title_overall_results = pd.concat(
            [title_overall_results, pd.DataFrame(columns=[keys])], axis=1
        )

    title_overall_results = pd.concat(
        [
            title_overall_results,
            pd.DataFrame(
                columns=[
                    LCOE,
                    ANNUITY,
                    NPV,
                    SUPPLY_RELIABILITY_KWH,
                    RES_SHARE,
                    AUTONOMY_FACTOR,
                    CO2_EMISSIONS_KGC02EQ,
                    TOTAL_EXCESS_ANNUAL_KWH,
                ]
            ),
        ],
        axis=1,
        sort=False,
    )

    if settings[RESULTS_DEMAND_CHARACTERISTICS] is True:
        title_overall_results = pd.concat(
            [
                title_overall_results,
                pd.DataFrame(
                    columns=[
                        TOTAL_DEMAND_ANNUAL_KWH,
                        DEMAND_PEAK_KW,
                        TOTAL_DEMAND_SUPPLIED_ANNUAL_KWH,
                        TOTAL_DEMAND_SHORTAGE_ANNUAL_KWH,
                    ]
                ),
            ],
            axis=1,
            sort=False,
        )
        """
        'total_demand_ac'
        'peak_demand_ac'
        'total_demand_dc'
        'peak_demand_dc'
        'mean_demand_ac'
        'mean_demand_dc'
        'peak/mean_demand_ratio_ac'
        'peak/mean_demand_ratio_dc'
        """

    if settings[RESULTS_BLACKOUT_CHARACTERISTICS] is True:
        title_overall_results = pd.concat(
            [
                title_overall_results,
                pd.DataFrame(
                    columns=[
                        NATIONAL_GRID_RELIABILITY_H,
                        NATIONAL_GRID_TOTAL_BLACKOUT_DURATION,
                        NATIONAL_GRID_NUMBER_OF_BLACKOUTS,
                    ]
                ),
            ],
            axis=1,
            sort=False,
        )

    title_overall_results = pd.concat(
        [
            title_overall_results,
            pd.DataFrame(
                columns=[
                    CAPACITY_PV_KWP,
                    CAPACITY_STORAGE_KWH,
                    POWER_STORAGE_KW,
                    CAPACITY_RECTIFIER_AC_DC_KW,
                    CAPACITY_INVERTER_KW,
                    CAPACITY_WIND_KW,
                    CAPACITY_GENSET_KW,
                    CAPACITY_PCOUPLING_KW,
                    TOTAL_PV_GENERATION_KWH,
                    TOTAL_WIND_GENERATION_KWH,
                    TOTAL_GENSET_GENERATION_KWH,
                    CONSUMPTION_FUEL_ANNUAL_KWH,
                    CONSUMPTION_FUEL_ANNUAL_L,
                    GENSET_HOURS_OF_OPERATION,
                    CONSUMPTION_MAIN_GRID_MG_SIDE_ANNUAL_KWH,
                    FEEDIN_MAIN_GRID_MG_SIDE_ANNUAL_KWH,
                ]
            ),
        ],
        axis=1,
        sort=False,
    )

    if settings[RESULTS_ANNUITIES] is True:
        title_overall_results = pd.concat(
            [
                title_overall_results,
                pd.DataFrame(
                    columns=[
                        ANNUITY_PV,
                        ANNUITY_STORAGE,
                        ANNUITY_RECTIFIER_AC_DC,
                        ANNUITY_INVERTER_DC_AC,
                        ANNUITY_WIND,
                        ANNUITY_GENSET,
                        ANNUITY_PCOUPLING,
                        ANNUITY_DISTRIBUTION_GRID,
                        ANNUITY_PROJECT,
                        ANNUITY_MAINGRID_EXTENSION,
                    ]
                ),
            ],
            axis=1,
            sort=False,
        )

    title_overall_results = pd.concat(
        [
            title_overall_results,
            pd.DataFrame(
                columns=[
                    EXPENDITURES_FUEL_ANNUAL,
                    EXPENDITURES_MAIN_GRID_CONSUMPTION_ANNUAL,
                    EXPENDITURES_SHORTAGE_ANNUAL,
                    REVENUE_MAIN_GRID_FEEDIN_ANNUAL,
                ]
            ),
        ],
        axis=1,
        sort=False,
    )

    # Called costs because they include the operation, while they are also not the present value because
    # the variable costs are included in the oem
    if settings[RESULTS_COSTS] is True:
        title_overall_results = pd.concat(
            [
                title_overall_results,
                pd.DataFrame(
                    columns=[
                        COSTS_PV,
                        COSTS_STORAGE,
                        COSTS_RECTIFIER_AC_DC,
                        COSTS_INVERTER_DC_AC,
                        COSTS_WIND,
                        COSTS_GENSET,
                        COSTS_PCOUPLING,
                        COSTS_DISTRIBUTION_GRID,
                        COSTS_PROJECT,
                        FIRST_INVESTMENT,
                        OPERATION_MAINTAINANCE_EXPENDITURES,
                        COSTS_MAINGRID_EXTENSION,
                        EXPENDITURES_FUEL_TOTAL,
                        EXPENDITURES_MAIN_GRID_CONSUMPTION_TOTAL,
                        EXPENDITURES_SHORTAGE_TOTAL,
                        REVENUE_MAIN_GRID_FEEDIN_TOTAL,
                    ]
                ),
            ],
            axis=1,
            sort=False,
        )

    title_overall_results = pd.concat(
        [
            title_overall_results,
            pd.DataFrame(
                columns=[
                    OBJECTIVE_VALUE,
                    SIMULATION_TIME,
                    EVALUATION_TIME,
                    FILENAME,
                    COMMENTS,
                ]
            ),
        ],
        axis=1,
        sort=False,
    )

    return title_overall_results
