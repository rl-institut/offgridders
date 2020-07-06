"""
Overlying script for tool for the analysis of possible
operational modes of micro grids interconnecting with an unreliable national grid

General settings from config.py, simulation-specific input data taken from dictionary experiment

Utilizing the bus/component library oemof_generatemodel and the process oemof library oemof_general
new cases can easily be added.
"""

# to check for files and paths
import os.path
import pprint as pp

# Logging of info
import logging

# This is not really a necessary class, as the whole experiement could be given to the function, but it ensures, that
# only correct input data is included

def update_dict(capacities_oem, specific_case, experiment):
    experiment_case_dict = {}

    experiment_case_dict.update(
        {
            "case_name": specific_case["case_name"],
            "filename": specific_case["case_name"]
            + experiment[
                "filename"
            ],  # experiment['output_folder'] + "_" + specific_case['case_name'] + experiment['filename']
            "total_demand_ac": experiment["total_demand_ac"],
            "total_demand_dc": experiment["total_demand_dc"],
            "peak_demand": experiment["abs_peak_demand_ac_side"],
            "evaluated_days": experiment["evaluated_days"],
            "genset_with_minimal_loading": specific_case[
                "genset_with_minimal_loading"
            ],
        }
    )

    warning_string = (
        "Invalid case definitions. For case " + specific_case["case_name"]
    )

    ###########################################
    # Define capacities                       #
    ###########################################
    # pv, storage, genset, wind, pcc consumption/feedin
    list_base_capacities = [
        "capacity_storage_kWh",
        "power_storage_kW",
        "capacity_genset_kW",
        "capacity_pv_kWp",
        "capacity_pcc_consumption_kW",
        "capacity_pcc_feedin_kW",
        "capacity_wind_kW",
        "capacity_rectifier_ac_dc_kW",
        "capacity_inverter_dc_ac_kW",
    ]
    list_of_batch_names = [
        "storage_batch_capacity",
        "storage_batch_power",
        "genset_batch",
        "pv_batch",
        "pcoupling_batch",  # check entry
        "pcoupling_batch",  # check entry
        "wind_batch",
        "rectifier_ac_dc_batch",
        "inverter_dc_ac_batch",
    ]  # create entry
    list_build_oemof_names = [
        "storage_fixed_capacity",
        "storage_fixed_power",
        "genset_fixed_capacity",
        "pv_fixed_capacity",
        "pcc_consumption_fixed_capacity",
        "pcc_feedin_fixed_capacity",
        "wind_fixed_capacity",
        "rectifier_ac_dc_fixed_capacity",
        "inverter_dc_ac_fixed_capacity",
    ]

    if len(list_base_capacities) != len(list_build_oemof_names):
        logging.warning("Lists for defining experiment cases not of same lenght.")

    for item in range(0, len(list_base_capacities)):
        if (
            list_base_capacities[item] == "power_storage_kW"
        ):  # it is not possible to set the optimization ect. of the storage power; the setting of storage will be used
            case_dict_entry = specific_case["capacity_storage_kWh"]
        else:
            case_dict_entry = specific_case[list_base_capacities[item]]
        component_name = list_base_capacities[item]
        #  next 3 lines not beautifully defined, could be one funtion in total
        case_dict_capacity = get_base_capacity(
            experiment_case_dict,
            case_dict_entry,
            capacities_oem,
            component_name,
            experiment[list_of_batch_names[item]],
        )
        # Correction factor for oversizing generator and pcc by factor (and include inefficiency of transformer)
        if case_dict_entry == "peak_demand":
            if component_name == "capacity_genset_kW":
                case_dict_capacity = (
                    case_dict_capacity * experiment["genset_oversize_factor"]
                )
            elif (
                component_name == "capacity_pcc_consumption_kW"
                or component_name == "capacity_pcc_feedin_kW"
            ):
                case_dict_capacity = round(
                    case_dict_capacity
                    / experiment["pcoupling_efficiency"]
                    * experiment["pcoupling_oversize_factor"],
                    3,
                )

        define_capacity(
            experiment_case_dict, case_dict_capacity, list_build_oemof_names[item]
        )

    ###########################################
    # Allowing shortage, define max. shortage #
    ###########################################
    if specific_case["allow_shortage"] == "default":
        experiment_case_dict.update(
            {"allow_shortage": experiment["allow_shortage"]}
        )
        experiment_case_dict.update(
            {"max_shortage": experiment["shortage_max_allowed"]}
        )

    elif specific_case["allow_shortage"] is False:
        experiment_case_dict.update({"allow_shortage": False})
        experiment_case_dict.update({"max_shortage": 0})

    elif (
        specific_case["allow_shortage"] == True
        and specific_case["max_shortage"] == "default"
    ):
        experiment_case_dict.update({"allow_shortage": True})
        experiment_case_dict.update(
            {"max_shortage": experiment["shortage_max_allowed"]}
        )

    elif specific_case["allow_shortage"] == True:
        if isinstance(specific_case["max_shortage"], float) or isinstance(
            specific_case["max_shortage"], int
        ):
            experiment_case_dict.update({"allow_shortage": True})
            experiment_case_dict.update(
                {"max_shortage": specific_case["max_shortage"]}
            )

    else:
        logging.warning(
            warning_string
            + ' values "allow_shortage" (True/False/default) and "max_shortage" (float/default) not defined properly: '
            + str(specific_case["allow_shortage"])
            + str(isinstance(specific_case["allow_shortage"], str))
        )

    ###########################################
    # Include stability constraint            #
    ###########################################

    if (
        specific_case["stability_constraint"] is False
        or specific_case["stability_constraint"] == "share_backup"
        or specific_case["stability_constraint"] == "share_usage"
        or specific_case["stability_constraint"] == "share_hybrid"
    ):
        experiment_case_dict.update(
            {"stability_constraint": specific_case["stability_constraint"]}
        )
    else:
        logging.warning(
            warning_string
            + ' value "stability_constraint" (False/share_backup/share_usage) not defined properly'
        )

    ###########################################
    # Include renewable constraint            #
    ###########################################

    if specific_case["renewable_constraint"] == "default":
        if experiment["min_renewable_share"] == 0:
            experiment_case_dict.update({"renewable_share_constraint": False})
        else:
            experiment_case_dict.update({"renewable_share_constraint": True})

    elif specific_case["renewable_constraint"] is False:
        experiment_case_dict.update({"renewable_share_constraint": False})

    elif specific_case["renewable_constraint"] == True:
        experiment_case_dict.update({"renewable_share_constraint": True})
    else:
        logging.warning(
            warning_string
            + ' value "renewable_share_constraint" (True/False/default) not defined properly'
        )

    experiment_case_dict["number_of_equal_generators"] = specific_case[
        "number_of_equal_generators"
    ]
    experiment_case_dict["evaluation_perspective"] = specific_case[
        "evaluation_perspective"
    ]
    experiment_case_dict["force_charge_from_maingrid"] = specific_case[
        "force_charge_from_maingrid"
    ]
    experiment_case_dict["discharge_only_when_blackout"] = specific_case[
        "discharge_only_when_blackout"
    ]
    experiment_case_dict["enable_inverter_only_at_backout"] = specific_case[
        "enable_inverter_only_at_backout"
    ]
    return experiment_case_dict

def get_base_capacity(
    experiment_case_dict, case_dict_entry, capacities, component_name, batch_size
):
    if case_dict_entry == "oem":
        case_dict_capacity = "oem"
    elif case_dict_entry == None or case_dict_entry == "None":
        case_dict_capacity = None
    elif isinstance(case_dict_entry, float) or isinstance(case_dict_entry, int):
        case_dict_capacity = case_dict_entry
    elif case_dict_entry == "peak_demand":
        case_dict_capacity = round(experiment_case_dict["peak_demand"], 3)
        case_dict_capacity = float(case_dict_capacity)
    elif case_dict_entry in capacities:
        case_dict_capacity = capacities[case_dict_entry][component_name]
        case_dict_capacity = (
            round(0.5 + case_dict_capacity / batch_size) * batch_size
        )
        case_dict_capacity = float(case_dict_capacity)
    else:
        logging.warning(
            "Invalid value of " + component_name + " with value " + case_dict_entry
        )

    return case_dict_capacity

def define_capacity(experiment_case_dict, case_dict_capacity, oemof_name):

    if case_dict_capacity == "oem":
        experiment_case_dict.update({oemof_name: False})
    elif case_dict_capacity == None or case_dict_capacity == 0:
        experiment_case_dict.update({oemof_name: None})
    elif isinstance(case_dict_capacity, float) or isinstance(
        case_dict_capacity, int
    ):
        experiment_case_dict.update({oemof_name: case_dict_capacity})
    else:
        logging.warning(
            "Invalid value of " + oemof_name + " with value " + case_dict_capacity
        )

    return
