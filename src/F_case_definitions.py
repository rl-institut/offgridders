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

from src.constants import (
    CASE_NAME,
    FILENAME,
    TOTAL_DEMAND_AC,
    TOTAL_DEMAND_DC,
    ABS_PEAK_DEMAND_AC_SIDE,
    EVALUATED_DAYS,
    GENSET_WITH_MINIMAL_LOADING,
    CAPACITY_PV_KWP,
    CAPACITY_WIND_KW,
    CAPACITY_RECTIFIER_AC_DC_KW,
    CAPACITY_INVERTER_DC_AC_KW,
    SHORTAGE_BATCH_CAPACITY,
    SHORTAGE_BATCH_POWER,
    GENSET_BATCH,
    PV_BATCH,
    PCOUPLING_BATCH,
    WIND_BATCH,
    RECTIFIER_AC_DC_BATCH,
    INVERTER_DC_AC_BATCH,
    STORAGE_FIXED_CAPACITY,
    STORAGE_FIXED_POWER,
    GENSET_FIXED_CAPACITY,
    PV_FIXED_CAPACITY,
    PCC_CONSUMPTION_FIXED_CAPACITY,
    PCC_FEEDIN_FIXED_CAPACITY,
    WIND_FIXED_CAPACITY,
    RECTIFIER_AC_DC_FIXED_CAPACITY,
    INVERTER_DC_AC_FIXED_CAPACITY,
    POWER_STORAGE_KW,
    CAPACITY_STORAGE_KWH,
    CAPACITY_GENSET_KW,
    GENSET_OVERSIZE_FACTOR,
    CAPACITY_PCC_CONSUMPTION_KW,
    CAPACITY_PCC_FEEDING_KW,
    PCOUPLING_OVERSIZE_FACTOR,
    ALLOW_SHORTAGE,
    SHORTAGE_MAX_ALLOWED,
    MAX_SHORTAGE,
    STABILITY_CONSTRAINT,
    RENEWABLE_CONSTRAINT,
    MIN_RENEWABLE_SHARE,
    RENEWABLE_SHARE_CONSTRAINT,
    NUMBER_OF_EQUAL_GENERATORS,
    EVALUATION_PERSPECTIVE,
    FORCE_CHARGE_FROM_MAINGRID,
    DISCHARGE_ONLY_WHEN_BLACKOUT,
    ENABLE_INVERTER_ONLY_AT_BLACKOUT,
    OEM,
    PEAK_DEMAND,
    PCOUPLING_EFFICIENCY,
    SHARE_BACKUP,
    SHARE_USAGE,
    SHARE_HYBRID,
    DEFAULT,
)

# This is not really a necessary class, as the whole experiement could be given to the function, but it ensures, that
# only correct input data is included


def update_dict(capacities_oem, specific_case, experiment):
    """
    Creates a dictionary containing all the details for the specific simulation

    Parameters
    ----------
    capacities_oem: dict
        Contains the capacities of the system as well as their characteristics

    specific_case: dict
        Contains details for the case name and definition

    experiment: dict
        Settings for the experiment

    Returns
    -------
    experiment_case_dict: dict
        Contains detailed information about the experiment's settings
    """
    experiment_case_dict = {}

    experiment_case_dict.update(
        {
            CASE_NAME: specific_case[CASE_NAME],
            FILENAME: specific_case[CASE_NAME]
            + experiment[
                FILENAME
            ],  # experiment['output_folder'] + "_" + specific_case['case_name'] + experiment['filename']
            TOTAL_DEMAND_AC: experiment[TOTAL_DEMAND_AC],
            TOTAL_DEMAND_DC: experiment[TOTAL_DEMAND_DC],
            PEAK_DEMAND: experiment[ABS_PEAK_DEMAND_AC_SIDE],
            EVALUATED_DAYS: experiment[EVALUATED_DAYS],
            GENSET_WITH_MINIMAL_LOADING: specific_case[GENSET_WITH_MINIMAL_LOADING],
        }
    )

    warning_string = "Invalid case definitions. For case " + specific_case[CASE_NAME]

    ###########################################
    # Define capacities                       #
    ###########################################
    # pv, storage, genset, wind, pcc consumption/feedin
    list_base_capacities = [
        CAPACITY_STORAGE_KWH,
        POWER_STORAGE_KW,
        CAPACITY_GENSET_KW,
        CAPACITY_PV_KWP,
        CAPACITY_PCC_CONSUMPTION_KW,
        CAPACITY_PCC_FEEDING_KW,
        CAPACITY_WIND_KW,
        CAPACITY_RECTIFIER_AC_DC_KW,
        CAPACITY_INVERTER_DC_AC_KW,
    ]
    list_of_batch_names = [
        SHORTAGE_BATCH_CAPACITY,
        SHORTAGE_BATCH_POWER,
        GENSET_BATCH,
        PV_BATCH,
        PCOUPLING_BATCH,  # check entry
        PCOUPLING_BATCH,  # check entry
        WIND_BATCH,
        RECTIFIER_AC_DC_BATCH,
        INVERTER_DC_AC_BATCH,
    ]  # create entry
    list_build_oemof_names = [
        STORAGE_FIXED_CAPACITY,
        STORAGE_FIXED_POWER,
        GENSET_FIXED_CAPACITY,
        PV_FIXED_CAPACITY,
        PCC_CONSUMPTION_FIXED_CAPACITY,
        PCC_FEEDIN_FIXED_CAPACITY,
        WIND_FIXED_CAPACITY,
        RECTIFIER_AC_DC_FIXED_CAPACITY,
        INVERTER_DC_AC_FIXED_CAPACITY,
    ]

    if len(list_base_capacities) != len(list_build_oemof_names):
        logging.warning("Lists for defining experiment cases not of same lenght.")

    for item in range(0, len(list_base_capacities)):
        if (
            list_base_capacities[item] == POWER_STORAGE_KW
        ):  # it is not possible to set the optimization ect. of the storage power; the setting of storage will be used
            case_dict_entry = specific_case[CAPACITY_STORAGE_KWH]
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
        if case_dict_entry == PEAK_DEMAND:
            if component_name == CAPACITY_GENSET_KW:
                case_dict_capacity = (
                    case_dict_capacity * experiment[GENSET_OVERSIZE_FACTOR]
                )
            elif (
                component_name == CAPACITY_PCC_CONSUMPTION_KW
                or component_name == CAPACITY_PCC_FEEDING_KW
            ):
                case_dict_capacity = round(
                    case_dict_capacity
                    / experiment[PCOUPLING_EFFICIENCY]
                    * experiment[PCOUPLING_OVERSIZE_FACTOR],
                    3,
                )

        define_capacity(
            experiment_case_dict, case_dict_capacity, list_build_oemof_names[item]
        )

    ###########################################
    # Allowing shortage, define max. shortage #
    ###########################################
    if specific_case[ALLOW_SHORTAGE] == DEFAULT:
        experiment_case_dict.update({ALLOW_SHORTAGE: experiment[ALLOW_SHORTAGE]})
        experiment_case_dict.update({MAX_SHORTAGE: experiment[SHORTAGE_MAX_ALLOWED]})

    elif specific_case[ALLOW_SHORTAGE] is False:
        experiment_case_dict.update({ALLOW_SHORTAGE: False})
        experiment_case_dict.update({MAX_SHORTAGE: 0})

    elif (
        specific_case[ALLOW_SHORTAGE] is True and specific_case[MAX_SHORTAGE] == DEFAULT
    ):
        experiment_case_dict.update({ALLOW_SHORTAGE: True})
        experiment_case_dict.update({MAX_SHORTAGE: experiment[SHORTAGE_MAX_ALLOWED]})

    elif specific_case[ALLOW_SHORTAGE] is True:
        if isinstance(specific_case[MAX_SHORTAGE], float) or isinstance(
            specific_case[MAX_SHORTAGE], int
        ):
            experiment_case_dict.update({ALLOW_SHORTAGE: True})
            experiment_case_dict.update({MAX_SHORTAGE: specific_case[MAX_SHORTAGE]})

    else:
        logging.warning(
            warning_string
            + f" values {ALLOW_SHORTAGE} (True/False/default) and {MAX_SHORTAGE} (float/default) not defined properly: "
            + str(specific_case[ALLOW_SHORTAGE])
            + str(isinstance(specific_case[ALLOW_SHORTAGE], str))
        )

    ###########################################
    # Include stability constraint            #
    ###########################################

    if (
        specific_case[STABILITY_CONSTRAINT] is False
        or specific_case[STABILITY_CONSTRAINT] == SHARE_BACKUP
        or specific_case[STABILITY_CONSTRAINT] == SHARE_USAGE
        or specific_case[STABILITY_CONSTRAINT] == SHARE_HYBRID
    ):
        experiment_case_dict.update(
            {STABILITY_CONSTRAINT: specific_case[STABILITY_CONSTRAINT]}
        )
    else:
        logging.warning(
            warning_string
            + f" value {STABILITY_CONSTRAINT} (False/share_backup/share_usage) not defined properly"
        )

    ###########################################
    # Include renewable constraint            #
    ###########################################

    if specific_case[RENEWABLE_CONSTRAINT] == DEFAULT:
        if experiment[MIN_RENEWABLE_SHARE] == 0:
            experiment_case_dict.update({RENEWABLE_SHARE_CONSTRAINT: False})
        else:
            experiment_case_dict.update({RENEWABLE_SHARE_CONSTRAINT: True})

    elif specific_case[RENEWABLE_CONSTRAINT] is False:
        experiment_case_dict.update({RENEWABLE_SHARE_CONSTRAINT: False})

    elif specific_case[RENEWABLE_CONSTRAINT] is True:
        experiment_case_dict.update({RENEWABLE_SHARE_CONSTRAINT: True})
    else:
        logging.warning(
            warning_string
            + f" value {RENEWABLE_SHARE_CONSTRAINT} (True/False/default) not defined properly"
        )

    experiment_case_dict[NUMBER_OF_EQUAL_GENERATORS] = specific_case[
        NUMBER_OF_EQUAL_GENERATORS
    ]
    experiment_case_dict[EVALUATION_PERSPECTIVE] = specific_case[EVALUATION_PERSPECTIVE]
    experiment_case_dict[FORCE_CHARGE_FROM_MAINGRID] = specific_case[
        FORCE_CHARGE_FROM_MAINGRID
    ]
    experiment_case_dict[DISCHARGE_ONLY_WHEN_BLACKOUT] = specific_case[
        DISCHARGE_ONLY_WHEN_BLACKOUT
    ]
    experiment_case_dict[ENABLE_INVERTER_ONLY_AT_BLACKOUT] = specific_case[
        ENABLE_INVERTER_ONLY_AT_BLACKOUT
    ]
    return experiment_case_dict


def get_base_capacity(
    experiment_case_dict, case_dict_entry, capacities, component_name, batch_size
):
    """
    Read or calculate the base capacity by looking at components or previous results

    Parameters
    ----------
    experiment_case_dict: dict
        Contains detailed information about the experiment's settings

    case_dict_entry: str or int/float
        Value for capacities or reference to them

    capacities: dict
        Contains capacities in the system

    component_name: str
        Name of the component from which its capacity will be extracted

    batch_size: float
        Undividable units that an asset can be installed as

    Returns
    -------
    case_dict_capacity: str or int/float
        Base capacity of the simulation

    """
    if case_dict_entry == OEM:
        case_dict_capacity = OEM
    elif case_dict_entry == None or case_dict_entry == "None":
        case_dict_capacity = None
    elif isinstance(case_dict_entry, float) or isinstance(case_dict_entry, int):
        case_dict_capacity = case_dict_entry
    elif case_dict_entry == PEAK_DEMAND:
        case_dict_capacity = round(experiment_case_dict[PEAK_DEMAND], 3)
        case_dict_capacity = float(case_dict_capacity)
    elif case_dict_entry in capacities:
        case_dict_capacity = capacities[case_dict_entry][component_name]
        case_dict_capacity = round(0.5 + case_dict_capacity / batch_size) * batch_size
        case_dict_capacity = float(case_dict_capacity)
    else:
        logging.warning(
            "Invalid value of " + component_name + " with value " + case_dict_entry
        )

    return case_dict_capacity


def define_capacity(experiment_case_dict, case_dict_capacity, oemof_name):
    """
    Updates the simulation information of a scenario with the capacities that each asset should already have pre-installed

    Depends on whether assets in the scenario are to be optimized or if the capacity is determined based on a previous, but different scenario.
        Parameters
        ----------
        experiment_case_dict: dict
            Contains detailed information about the experiment's settings

        case_dict_capacity: str or int/float
            Base capacity of the simulation

        oemof_name: str
            Name of the oemof simulation

        Returns
        -------
    """
    if case_dict_capacity == OEM:
        experiment_case_dict.update({oemof_name: False})
    elif case_dict_capacity == None or case_dict_capacity == 0:
        experiment_case_dict.update({oemof_name: None})
    elif isinstance(case_dict_capacity, float) or isinstance(case_dict_capacity, int):
        experiment_case_dict.update({oemof_name: case_dict_capacity})
    else:
        logging.warning(
            "Invalid value of " + oemof_name + " with value " + case_dict_capacity
        )

    return
