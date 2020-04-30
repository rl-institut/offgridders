"""
This script creates all possible sensitivity_experiment_s of a sensitivity analysis with a list of sensitive parameters
(bound by min, max, step lenght) and a list of constant parameters. All parameters are stored in a large
dictonary, including filenames.
"""

import pandas as pd
import logging

import itertools
import numpy as np
from copy import deepcopy

# todo: this module should not be called here
try:
    from .D0_process_input import process_input_parameters
except ModuleNotFoundError:
    from code_folder.D0_process_input import process_input_parameters


class generate_sensitvitiy_experiments:
    def get(
        settings, parameters_constant_values, parameters_sensitivity, project_sites
    ):
        #######################################################
        # Get sensitivity_experiment_s for sensitivity analysis            #
        #######################################################
        if settings["sensitivity_all_combinations"] == True:
            (
                sensitivitiy_experiment_s,
                number_of_project_sites,
                sensitivity_array_dict,
                total_number_of_experiments,
            ) = generate_experiments.all_possible(
                settings,
                parameters_constant_values,
                parameters_sensitivity,
                project_sites,
            )

        elif settings["sensitivity_all_combinations"] == False:
            (
                sensitivitiy_experiment_s,
                number_of_project_sites,
                sensitivity_array_dict,
                total_number_of_experiments,
            ) = generate_experiments.with_base_case(
                settings,
                parameters_constant_values,
                parameters_sensitivity,
                project_sites,
            )

        else:
            logging.warning(
                'Setting "sensitivity_all_combinations" not valid! Has to be TRUE or FALSE.'
            )

        names_sensitivities = [key for key in sensitivity_array_dict.keys()]

        message = "Parameters of sensitivity analysis: "
        for entry in names_sensitivities:
            message += entry + ", "

        logging.info(message[:-2])

        for experiment in sensitivitiy_experiment_s:
            helpers.test_techno_economical_parameters_complete(
                sensitivitiy_experiment_s[experiment]
            )

            # scaling demand according to scaling factor - used for tests regarding tool application
            sensitivitiy_experiment_s[experiment].update(
                {
                    "demand_ac": sensitivitiy_experiment_s[experiment]["demand_ac"]
                    * sensitivitiy_experiment_s[experiment]["demand_ac_scaling_factor"]
                }
            )
            sensitivitiy_experiment_s[experiment].update(
                {
                    "demand_dc": sensitivitiy_experiment_s[experiment]["demand_dc"]
                    * sensitivitiy_experiment_s[experiment]["demand_dc_scaling_factor"]
                }
            )

            #  Add economic values to sensitivity sensitivity_experiment_s
            process_input_parameters.economic_values(
                sensitivitiy_experiment_s[experiment]
            )
            # Give a file item to the sensitivity_experiment_s
            get_names.experiment_name(
                sensitivitiy_experiment_s[experiment],
                sensitivity_array_dict,
                number_of_project_sites,
            )

            if "comments" not in sensitivitiy_experiment_s[experiment]:
                sensitivitiy_experiment_s[experiment].update({"comments": ""})

            if sensitivitiy_experiment_s[experiment]["storage_soc_initial"] == "None":
                sensitivitiy_experiment_s[experiment].update(
                    {"storage_soc_initial": None}
                )
        #######################################################
        # Get blackout_experiment_s for sensitvitiy           #
        #######################################################
        # Creating dict of possible blackout scenarios (combinations of durations  frequencies
        (
            blackout_experiment_s,
            blackout_experiments_count,
        ) = generate_experiments.blackout(
            sensitivity_array_dict, parameters_constant_values, settings
        )

        # save all Experiments with all used input data to csv
        csv_dict = deepcopy(sensitivitiy_experiment_s)
        # delete timeseries to make file readable
        timeseries_names = [
            "demand_ac",
            "demand_dc",
            "pv_generation_per_kWp",
            "wind_generation_per_kW",
            "grid_availability",
        ]
        for entry in csv_dict:
            for series in timeseries_names:
                if series in csv_dict[entry].keys():
                    del csv_dict[entry][series]

        experiments_dataframe = pd.DataFrame.from_dict(csv_dict, orient="index")
        experiments_dataframe.to_csv(
            settings["output_folder"] + "/simulation_experiments.csv"
        )

        for item in experiments_dataframe.columns:
            if (item not in parameters_sensitivity.keys()) and (
                item not in ["project_site_name"]
            ):
                experiments_dataframe = experiments_dataframe.drop(columns=item)

        experiments_dataframe.to_csv(
            settings["output_folder"] + "/sensitivity_experiments.csv"
        )

        # Generate a overall title of the oemof-results DataFrame
        title_overall_results = helpers.overall_results_title(
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

        settings.update({"total_number_of_experiments": total_number_of_experiments})

        return (
            sensitivitiy_experiment_s,
            blackout_experiment_s,
            title_overall_results,
            names_sensitivities,
        )


class generate_experiments:
    def all_possible(
        settings, parameters_constant_values, parameters_sensitivity, project_site_s
    ):
        # Deletes constants from parameters_constant_values depending on values defined in sensitivity
        remove_doubles.constants_senstivity(
            parameters_constant_values, parameters_sensitivity
        )
        # Deletes constants from parameters_constant_values depending on values defined in project sites
        remove_doubles.constants_project_sites(
            parameters_constant_values, project_site_s
        )
        # Deletes project site parameter that is also included in sensitivity analysis
        remove_doubles.project_sites_sensitivity(parameters_sensitivity, project_site_s)

        # From now on, universal parameters poses the base scenario. some parameters might only be set with project sites!
        universal_parameters, number_of_project_sites = get.universal_parameters(
            settings, parameters_constant_values, parameters_sensitivity, project_site_s
        )

        sensitivity_array_dict = get.dict_sensitivies_arrays(
            parameters_sensitivity, project_site_s
        )

        project_site_dict = {
            "project_site_name": [key for key in project_site_s.keys()]
        }
        (
            sensitivity_experiment_s,
            total_number_of_experiments,
        ) = get.all_possible_combinations(sensitivity_array_dict, project_site_dict)

        for experiment in sensitivity_experiment_s:
            sensitivity_experiment_s[experiment].update(deepcopy(universal_parameters))
            sensitivity_experiment_s[experiment].update(
                deepcopy(
                    project_site_s[
                        sensitivity_experiment_s[experiment]["project_site_name"]
                    ]
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
        remove_doubles.constants_project_sites(
            parameters_constant_values, project_site_s
        )

        universal_parameters, number_of_project_sites = get.universal_parameters(
            settings, parameters_constant_values, parameters_sensitivity, project_site_s
        )

        # From now on, universal parameters poses the base scenario. some parameters might only be set with project sites!
        sensitivity_array_dict = get.dict_sensitivies_arrays(
            parameters_sensitivity, project_site_s
        )

        (
            sensitivity_experiment_s,
            total_number_of_experiments,
        ) = get.combinations_around_base(
            sensitivity_array_dict, universal_parameters, project_site_s
        )

        return (
            sensitivity_experiment_s,
            number_of_project_sites,
            sensitivity_array_dict,
            total_number_of_experiments,
        )

    def blackout(sensitivity_array_dict, parameters_constants, settings):
        blackout_parameters = deepcopy(sensitivity_array_dict)
        for parameter in sensitivity_array_dict:
            if (
                parameter != "blackout_duration"
                and parameter != "blackout_frequency"
                and parameter != "blackout_duration_std_deviation"
                and parameter != "blackout_frequency_std_deviation"
            ):
                del blackout_parameters[parameter]

        blackout_constants = deepcopy(parameters_constants)
        for parameter in parameters_constants:
            if (
                parameter != "blackout_duration"
                and parameter != "blackout_frequency"
                and parameter != "blackout_duration_std_deviation"
                and parameter != "blackout_frequency_std_deviation"
                and parameter not in sensitivity_array_dict
            ):
                del blackout_constants[parameter]

        if settings["sensitivity_all_combinations"] == True:
            (
                blackout_experiment_s,
                blackout_experiments_count,
            ) = get.all_possible_combinations(blackout_parameters, {})
            for blackout_experiment in blackout_experiment_s:
                blackout_experiment_s[blackout_experiment].update(
                    deepcopy(blackout_constants)
                )

        elif settings["sensitivity_all_combinations"] == False:
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
                        and defined_base == False
                    ):
                        # Defining scenario only with base case values for universal parameter / specific to project site (once!)
                        blackout_experiments_count += 1
                        blackout_experiment_s.update(
                            {blackout_experiments_count: deepcopy(blackout_constants)}
                        )
                        blackout_experiment_s[blackout_experiments_count].update(
                            {key: key_value}
                        )
                        defined_base == True

            if len(blackout_experiment_s) == 0:
                blackout_experiments_count += 1
                blackout_experiment_s.update(
                    {blackout_experiments_count: deepcopy(blackout_constants)}
                )

        else:
            logging.warning(
                'Setting "sensitivity_all_combinations" not valid! Has to be TRUE or FALSE.'
            )

        # define file item to save simulation / get grid availabilities
        for blackout_experiment in blackout_experiment_s:
            blackout_experiment_name = get_names.blackout_experiment_name(
                blackout_experiment_s[blackout_experiment]
            )
            blackout_experiment_s[blackout_experiment].update(
                {"experiment_name": blackout_experiment_name}
            )

        # delete all doubled entries -> could also be applied to experiments!
        experiment_copy = deepcopy(blackout_experiment_s)

        for i in experiment_copy:
            for e in experiment_copy:

                if (
                    i != e
                    and experiment_copy[i]["experiment_name"]
                    == experiment_copy[e]["experiment_name"]
                ):
                    if i in blackout_experiment_s and e in blackout_experiment_s:
                        del blackout_experiment_s[e]

        logging.info(
            "Randomized blackout timeseries for all combinations of blackout duration and frequency ("
            + str(len(blackout_experiment_s))
            + " experiments) will be generated."
        )

        return blackout_experiment_s, blackout_experiments_count


class get:
    def universal_parameters(
        settings, parameters_constant_values, parameters_sensitivity, project_site_s
    ):
        # create base case
        universal_parameters = deepcopy(settings)
        universal_parameters.update(deepcopy(parameters_constant_values))

        number_of_project_sites = 0
        for key in project_site_s:
            number_of_project_sites += 1

        return universal_parameters, number_of_project_sites

    def dict_sensitivies_arrays(parameters_sensitivity, project_sites):
        # fill dictionary with all sensitivity ranges defining the different simulations of the sensitivity analysis
        # ! do not use a key two times, as it will be overwritten by new information
        sensitivity_array_dict = {}
        for keys in parameters_sensitivity:
            if (
                parameters_sensitivity[keys]["Min"]
                == parameters_sensitivity[keys]["Max"]
            ):
                sensitivity_array_dict.update(
                    {keys: np.array([parameters_sensitivity[keys]["Min"]])}
                )
            else:
                sensitivity_array_dict.update(
                    {
                        keys: np.arange(
                            parameters_sensitivity[keys]["Min"],
                            parameters_sensitivity[keys]["Max"]
                            + parameters_sensitivity[keys]["Step"] / 2,
                            parameters_sensitivity[keys]["Step"],
                        )
                    }
                )
        return sensitivity_array_dict

    def all_possible_combinations(sensitivity_array_dict, name_entry_dict):
        # create all possible combinations of sensitive parameters
        all_parameters = {}
        for key in sensitivity_array_dict:
            all_parameters.update(
                {key: [value for value in sensitivity_array_dict[key]]}
            )

        all_parameters.update(deepcopy(name_entry_dict))
        # create all possible combinations of sensitive parameters
        keys = [key for key in all_parameters.keys()]
        values = [all_parameters[key] for key in all_parameters.keys()]
        all_experiments = [dict(zip(keys, v)) for v in itertools.product(*values)]

        number_of_experiment = 0
        sensitivity_experiment_s = {}
        for experiment in all_experiments:
            number_of_experiment += 1
            sensitivity_experiment_s.update(
                {number_of_experiment: deepcopy(experiment)}
            )

        total_number_of_experiments = number_of_experiment

        return sensitivity_experiment_s, total_number_of_experiments

    def combinations_around_base(
        sensitivity_array_dict, universal_parameters, project_site_s
    ):

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
                    {"project_site_name": project_site}
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
                                {"project_site_name": project_site}
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
                            and defined_base == False
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
                                {"project_site_name": project_site}
                            )
                            sensitivity_experiment_s[experiment_number].update(
                                deepcopy(project_site_s[project_site])
                            )
                            defined_base = True
                            sensitivity_experiment_s[experiment_number].update(
                                {"comments": "Base case, "}
                            )

        total_number_of_experiments = experiment_number
        return sensitivity_experiment_s, total_number_of_experiments

    def project_site_experiments(sensitivity_experiment_s, project_sites):
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
                deepcopy(project_sites[experiment_s[experiment]["project_site_name"]])
            )

        return experiment_s, number_of_experiments


class get_names:
    def experiment_name(experiment, sensitivity_array_dict, number_of_project_sites):
        # define file postfix to save simulation
        filename = "_s"
        if number_of_project_sites > 1:
            if isinstance(experiment["project_site_name"], str):
                filename = filename + "_" + experiment["project_site_name"]
            else:
                filename = filename + "_" + str(experiment["project_site_name"])
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
        experiment.update({"filename": filename})
        return

    # Generate names for blackout sensitivity_experiment_s, used in sensitivity.blackoutexperiments and in maintool
    def blackout_experiment_name(blackout_experiment):
        blackout_experiment_name = (
            "blackout_dur"
            + "_"
            + str(round(float(blackout_experiment["blackout_duration"]), 3))
            + "_"
            + "dur_dev"
            + "_"
            + str(
                round(float(blackout_experiment["blackout_duration_std_deviation"]), 3)
            )
            + "_"
            + "freq"
            + "_"
            + str(round(float(blackout_experiment["blackout_frequency"]), 3))
            + "_"
            + "freq_dev"
            + "_"
            + str(
                round(float(blackout_experiment["blackout_frequency_std_deviation"]), 3)
            )
        )
        return blackout_experiment_name


class remove_doubles:
    def constants_project_sites(parameters_constant_values, project_sites):
        # remove all entries that are doubled in parameters_constant_values, settings & project_site_s from parameters_constant_values
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
        # remove all entries that are doubled in sensitivity_bounds/project_site_s from project site
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
        # remove all entries that are doubled in parameters_constant_values, settings & parameters_sensitivity
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


class helpers:
    def test_techno_economical_parameters_complete(experiment):
        parameter_list = {
            "blackout_duration": 0,
            "blackout_duration_std_deviation": 0,
            "blackout_frequency": 0,
            "blackout_frequency_std_deviation": 0,
            "combustion_value_fuel": 9.8,
            "demand_ac_scaling_factor": 1,
            "demand_dc_scaling_factor": 1,
            "distribution_grid_cost_investment": 0,
            "distribution_grid_cost_opex": 0,
            "distribution_grid_lifetime": 0,
            #'fuel_price': 0.76,
            #'fuel_price_change_annual': 0,
            "genset_batch": 1,
            "genset_cost_investment": 0,
            "genset_cost_opex": 0,
            "genset_cost_var": 0,
            "genset_efficiency": 0.33,
            "genset_lifetime": 15,
            "genset_max_loading": 1,
            "genset_min_loading": 0,
            "genset_oversize_factor": 1.2,
            "inverter_dc_ac_batch": 1,
            "inverter_dc_ac_cost_investment": 0,
            "inverter_dc_ac_cost_opex": 0,
            "inverter_dc_ac_cost_var": 0,
            "inverter_dc_ac_efficiency": 1,
            "inverter_dc_ac_lifetime": 15,
            "maingrid_distance": 0,
            "maingrid_electricity_price": 0.15,
            "maingrid_extension_cost_investment": 0,
            "maingrid_extension_cost_opex": 0,
            "maingrid_extension_lifetime": 40,
            "maingrid_feedin_tariff": 0,
            "maingrid_renewable_share": 0,
            "min_renewable_share": 0,
            "pcoupling_batch": 1,
            "pcoupling_cost_investment": 0,
            "pcoupling_cost_opex": 0,
            "pcoupling_cost_var": 0,
            "pcoupling_efficiency": 1,
            "pcoupling_lifetime": 15,
            "pcoupling_oversize_factor": 1.05,
            "price_fuel": 0.76,
            "project_cost_investment": 0,
            "project_cost_opex": 0,
            "project_lifetime": 20,
            "pv_batch": 1,
            "pv_cost_investment": 0,
            "pv_cost_opex": 0,
            "pv_cost_var": 0,
            "pv_lifetime": 20,
            "rectifier_ac_dc_batch": 1,
            "rectifier_ac_dc_cost_investment": 0,
            "rectifier_ac_dc_cost_opex": 0,
            "rectifier_ac_dc_cost_var": 0,
            "rectifier_ac_dc_efficiency": 1,
            "rectifier_ac_dc_lifetime": 15,
            "shortage_max_allowed": 0,
            "shortage_max_timestep": 1,
            "shortage_penalty_costs": 0.2,
            "stability_limit": 0.4,
            "storage_batch_capacity": 1,
            "storage_batch_power": 1,
            "storage_capacity_cost_investment": 0,
            "storage_capacity_cost_opex": 0,
            "storage_capacity_lifetime": 5,
            "storage_cost_var": 0,
            "storage_Crate_charge": 1,
            "storage_Crate_discharge": 1,
            "storage_efficiency_charge": 0.8,
            "storage_efficiency_discharge": 1,
            "storage_loss_timestep": 0,
            "storage_power_cost_investment": 0,
            "storage_power_cost_opex": 0,
            "storage_power_lifetime": 5,
            "storage_soc_initial": None,
            "storage_soc_max": 0.95,
            "storage_soc_min": 0.3,
            "tax": 0,
            "wacc": 0.09,
            "white_noise_demand": 0,
            "white_noise_pv": 0,
            "white_noise_wind": 0,
            "wind_batch": 1,
            "wind_cost_investment": 0,
            "wind_cost_opex": 0,
            "wind_cost_var": 0,
            "wind_lifetime": 15,
        }

        for parameter in parameter_list:
            if parameter not in experiment:
                if (
                    (parameter == "price_fuel")
                    and ("fuel_price" in experiment)
                    and ("fuel_price_change_annual" in experiment)
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

    def overall_results_title(
        settings, number_of_project_sites, sensitivity_array_dict
    ):
        logging.debug("Generating header for results.csv")
        title_overall_results = pd.DataFrame(columns=["case", "project_site_name"])

        for keys in sensitivity_array_dict:
            title_overall_results = pd.concat(
                [title_overall_results, pd.DataFrame(columns=[keys])], axis=1
            )

        title_overall_results = pd.concat(
            [
                title_overall_results,
                pd.DataFrame(
                    columns=[
                        "lcoe",
                        "annuity",
                        "npv",
                        "supply_reliability_kWh",
                        "res_share",
                        "autonomy_factor",
                    ]
                ),
            ],
            axis=1,
            sort=False,
        )

        if settings["results_demand_characteristics"] == True:
            title_overall_results = pd.concat(
                [
                    title_overall_results,
                    pd.DataFrame(
                        columns=[
                            "total_demand_annual_kWh",
                            "demand_peak_kW",
                            "total_demand_supplied_annual_kWh",
                            "total_demand_shortage_annual_kWh",
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

        if settings["results_blackout_characteristics"] == True:
            title_overall_results = pd.concat(
                [
                    title_overall_results,
                    pd.DataFrame(
                        columns=[
                            "national_grid_reliability_h",
                            "national_grid_total_blackout_duration",
                            "national_grid_number_of_blackouts",
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
                        "capacity_pv_kWp",
                        "capacity_storage_kWh",
                        "power_storage_kW",
                        "capacity_rectifier_ac_dc_kW",
                        "capacity_inverter_kW",
                        "capacity_wind_kW",
                        "capacity_genset_kW",
                        "capacity_pcoupling_kW",
                        "total_pv_generation_kWh",
                        "total_wind_generation_kWh",
                        "total_genset_generation_kWh",
                        "consumption_fuel_annual_l",
                        "consumption_main_grid_mg_side_annual_kWh",
                        "feedin_main_grid_mg_side_annual_kWh",
                    ]
                ),
            ],
            axis=1,
            sort=False,
        )

        if settings["results_annuities"] == True:
            title_overall_results = pd.concat(
                [
                    title_overall_results,
                    pd.DataFrame(
                        columns=[
                            "annuity_pv",
                            "annuity_storage",
                            "annuity_rectifier_ac_dc",
                            "annuity_inverter_dc_ac",
                            "annuity_wind",
                            "annuity_genset",
                            "annuity_pcoupling",
                            "annuity_distribution_grid",
                            "annuity_project",
                            "annuity_maingrid_extension",
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
                        "expenditures_fuel_annual",
                        "expenditures_main_grid_consumption_annual",
                        "expenditures_shortage_annual",
                        "revenue_main_grid_feedin_annual",
                    ]
                ),
            ],
            axis=1,
            sort=False,
        )

        # Called costs because they include the operation, while they are also not the present value because
        # the variable costs are included in the oem
        if settings["results_costs"] == True:
            title_overall_results = pd.concat(
                [
                    title_overall_results,
                    pd.DataFrame(
                        columns=[
                            "costs_pv",
                            "costs_storage",
                            "costs_rectifier_ac_dc",
                            "costs_inverter_dc_ac",
                            "costs_wind",
                            "costs_genset",
                            "costs_pcoupling",
                            "costs_distribution_grid",
                            "costs_project",
                            "first_investment",
                            "operation_mantainance_expenditures",
                            "costs_maingrid_extension",
                            "expenditures_fuel_total",
                            "expenditures_main_grid_consumption_total",
                            "expenditures_shortage_total",
                            "revenue_main_grid_feedin_total",
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
                        "objective_value",
                        "simulation_time",
                        "evaluation_time",
                        "filename",
                        "comments",
                    ]
                ),
            ],
            axis=1,
            sort=False,
        )

        return title_overall_results
