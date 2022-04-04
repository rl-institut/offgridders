import logging
import sys
import oemof.solph as solph
from oemof.solph import processing

import src.G2a_oemof_busses_and_componets as generate
import src.G2b_constraints_custom as constraints_custom

from src.constants import (
    BUS_FUEL,
    DATE_TIME_INDEX,
    BUS_ELECTRICITY_AC,
    DEMAND_PROFILE_AC,
    GENSET_FIXED_CAPACITY,
    GENSET_WITH_MINIMAL_LOADING,
    NUMBER_OF_EQUAL_GENERATORS,
    CASE_NAME,
    WIND_FIXED_CAPACITY,
    PCC_CONSUMPTION_FIXED_CAPACITY,
    PCC_FEEDIN_FIXED_CAPACITY,
    PEAK_DEMAND,
    BUS_ELECTRICITY_DC,
    DEMAND_PROFILE_DC,
    PV_FIXED_CAPACITY,
    STORAGE_FIXED_CAPACITY,
    STORAGE_FIXED_POWER,
    RECTIFIER_AC_DC_FIXED_CAPACITY,
    INVERTER_DC_AC_FIXED_CAPACITY,
    ALLOW_SHORTAGE,
    STABILITY_CONSTRAINT,
    SHARE_BACKUP,
    SHARE_USAGE,
    SHARE_HYBRID,
    CRITICAL,
    RENEWABLE_SHARE_CONSTRAINT,
    FORCE_CHARGE_FROM_MAINGRID,
    DISCHARGE_ONLY_WHEN_BLACKOUT,
    ENABLE_INVERTER_ONLY_AT_BLACKOUT,
    SOLVER,
    SAVE_LP_FILE,
    OUTPUT_FOLDER,
    MAIN,
    META,
    SOLVER_VERBOSE,
    CMDLINE_OPTION,
    CMDLINE_OPTION_VALUE,
    SYMBOLIC_SOLVER_LABELS,
    OEMOF_FOLDER,
    CASE_DEFINITIONS,
)


def load_energysystem_lp():
    # based on lp file
    return


def build(experiment, case_dict):

    """
    Creates an implementable model for the oemof optimization with the specs. dictionaries

    Parameters
    ----------
    experiment: dict
        Contains general settings for the experiment

    case_dict: dict
        Contains settings for capacities and storage

    Returns
    -------
    micro_grid_system: oemof.solph.network.EnergySystem
        Energy system for oemof optimization

    model: oemof.solph.models.Model
        Model used for the oemof optimization


    """
    logging.debug("Complete case dictionary:")
    logging.debug(case_dict)

    logging.debug("Create oemof model by adding case-specific busses and components.")

    # create energy system
    micro_grid_system = solph.EnergySystem(timeindex=experiment[DATE_TIME_INDEX])

    ###################################
    ## AC side of the energy system   #
    ###################################

    logging.debug("Added to oemof model: Electricity bus of energy system, AC")
    bus_electricity_ac = solph.Bus(label=BUS_ELECTRICITY_AC)
    micro_grid_system.add(bus_electricity_ac)

    # ------------demand sink ac------------#
    sink_demand_ac = generate.demand_ac(
        micro_grid_system, bus_electricity_ac, experiment[DEMAND_PROFILE_AC]
    )

    # ------------fuel source------------#
    if case_dict[GENSET_FIXED_CAPACITY] != None:
        logging.debug("Added to oemof model: Fuel bus")
        bus_fuel = solph.Bus(label=BUS_FUEL)
        micro_grid_system.add(bus_fuel)
        generate.fuel(micro_grid_system, bus_fuel, experiment)

    # ------------genset------------#
    if case_dict[GENSET_FIXED_CAPACITY] == None:
        genset = None
    elif case_dict[GENSET_FIXED_CAPACITY] is False:
        if case_dict[GENSET_WITH_MINIMAL_LOADING] is True:
            # not possible with oemof
            logging.error(
                "It is not possible to optimize a generator with minimal loading in oemof. \n "
                + "    "
                + "    "
                + "    "
                + f"Please set {GENSET_WITH_MINIMAL_LOADING}=False for this case on tab {CASE_DEFINITIONS} in the excel template."
            )
            sys.exit()
            # genset = generate.genset_oem_minload(micro_grid_system, bus_fuel, bus_electricity_ac, experiment, case_dict['number_of_equal_generators'])
        else:
            genset = generate.genset_oem(
                micro_grid_system,
                bus_fuel,
                bus_electricity_ac,
                experiment,
                case_dict[NUMBER_OF_EQUAL_GENERATORS],
            )

    elif isinstance(case_dict[GENSET_FIXED_CAPACITY], float):
        if case_dict[GENSET_WITH_MINIMAL_LOADING] is True:
            genset = generate.genset_fix_minload(
                micro_grid_system,
                bus_fuel,
                bus_electricity_ac,
                experiment,
                capacity_fuel_gen=case_dict[GENSET_FIXED_CAPACITY],
                number_of_equal_generators=case_dict[NUMBER_OF_EQUAL_GENERATORS],
            )
        else:
            genset = generate.genset_fix(
                micro_grid_system,
                bus_fuel,
                bus_electricity_ac,
                experiment,
                capacity_fuel_gen=case_dict[GENSET_FIXED_CAPACITY],
                number_of_equal_generators=case_dict[NUMBER_OF_EQUAL_GENERATORS],
            )
    else:
        logging.warning(
            "Case definition of "
            + case_dict[CASE_NAME]
            + " faulty at genset_fixed_capacity. Value can only be False, float or None"
        )

    # ------------wind------------#
    if case_dict[WIND_FIXED_CAPACITY] == None:
        wind_plant = None
    elif case_dict[WIND_FIXED_CAPACITY] is False:
        wind_plant = generate.wind_oem(
            micro_grid_system, bus_electricity_ac, experiment
        )

    elif isinstance(case_dict[WIND_FIXED_CAPACITY], float):
        wind_plant = generate.wind_fix(
            micro_grid_system,
            bus_electricity_ac,
            experiment,
            capacity_wind=case_dict[WIND_FIXED_CAPACITY],
        )

    else:
        logging.warning(
            "Case definition of "
            + case_dict[CASE_NAME]
            + " faulty at wind_fixed_capacity. Value can only be False, float or None"
        )

    # ------------ main grid bus and subsequent sources if necessary------------#
    if case_dict[PCC_CONSUMPTION_FIXED_CAPACITY] != None:
        # source + sink for electricity from grid
        bus_electricity_ng_consumption = generate.maingrid_consumption(
            micro_grid_system, experiment
        )

    if case_dict[PCC_FEEDIN_FIXED_CAPACITY] != None:
        # sink + source for feed-in
        bus_electricity_ng_feedin = generate.maingrid_feedin(
            micro_grid_system, experiment
        )

    # ------------point of coupling (consumption)------------#
    if case_dict[PCC_CONSUMPTION_FIXED_CAPACITY] == None:
        pointofcoupling_consumption = None
    elif case_dict[PCC_CONSUMPTION_FIXED_CAPACITY] is False:
        pointofcoupling_consumption = generate.pointofcoupling_consumption_oem(
            micro_grid_system,
            bus_electricity_ac,
            bus_electricity_ng_consumption,
            experiment,
            min_cap_pointofcoupling=case_dict[PEAK_DEMAND],
        )
    elif isinstance(case_dict[PCC_CONSUMPTION_FIXED_CAPACITY], float):
        pointofcoupling_consumption = generate.pointofcoupling_consumption_fix(
            micro_grid_system,
            bus_electricity_ac,
            bus_electricity_ng_consumption,
            experiment,
            cap_pointofcoupling=case_dict[PCC_CONSUMPTION_FIXED_CAPACITY],
        )
    else:
        logging.warning(
            "Case definition of "
            + case_dict[CASE_NAME]
            + " faulty at pcc_consumption_fixed_capacity. Value can only be False, float or None"
        )

    # ------------point of coupling (feedin)------------#
    if case_dict[PCC_FEEDIN_FIXED_CAPACITY] == None:
        pass
        # pointofcoupling_feedin = None
    elif case_dict[PCC_FEEDIN_FIXED_CAPACITY] is False:
        generate.pointofcoupling_feedin_oem(
            micro_grid_system,
            bus_electricity_ac,
            bus_electricity_ng_feedin,
            experiment,
            min_cap_pointofcoupling=case_dict[PEAK_DEMAND],
        )

    elif isinstance(case_dict[PCC_FEEDIN_FIXED_CAPACITY], float):
        generate.pointofcoupling_feedin_fix(
            micro_grid_system,
            bus_electricity_ac,
            bus_electricity_ng_feedin,
            experiment,
            capacity_pointofcoupling=case_dict[PCC_FEEDIN_FIXED_CAPACITY],
        )
    else:
        logging.warning(
            "Case definition of "
            + case_dict[CASE_NAME]
            + " faulty at pcc_feedin_fixed_capacity. Value can only be False, float or None"
        )

    ###################################
    ## DC side of the energy system   #
    ###################################

    # ------------DC electricity bus------------#
    logging.debug("Added to oemof model: Electricity bus of energy system, DC")
    bus_electricity_dc = solph.Bus(label=BUS_ELECTRICITY_DC)
    micro_grid_system.add(bus_electricity_dc)

    # ------------demand sink dc------------#
    sink_demand_dc = generate.demand_dc(
        micro_grid_system, bus_electricity_dc, experiment[DEMAND_PROFILE_DC]
    )

    # ------------PV------------#
    if case_dict[PV_FIXED_CAPACITY] == None:
        solar_plant = None
    elif case_dict[PV_FIXED_CAPACITY] is False:
        solar_plant = generate.pv_oem(micro_grid_system, bus_electricity_dc, experiment)

    elif isinstance(case_dict[PV_FIXED_CAPACITY], float):
        solar_plant = generate.pv_fix(
            micro_grid_system,
            bus_electricity_dc,
            experiment,
            capacity_pv=case_dict[PV_FIXED_CAPACITY],
        )

    else:
        logging.warning(
            "Case definition of "
            + case_dict[CASE_NAME]
            + " faulty at pv_fixed_capacity. Value can only be False, float or None"
        )

    # ------------storage------------#
    if case_dict[STORAGE_FIXED_CAPACITY] == None:
        storage = None
    elif case_dict[STORAGE_FIXED_CAPACITY] is False:
        storage = generate.storage_oem(
            micro_grid_system, bus_electricity_dc, experiment
        )

    elif isinstance(case_dict[STORAGE_FIXED_CAPACITY], float):
        storage = generate.storage_fix(
            micro_grid_system,
            bus_electricity_dc,
            experiment,
            capacity_storage=case_dict[STORAGE_FIXED_CAPACITY],
            power_storage=case_dict[STORAGE_FIXED_POWER],
        )  # changed order

    else:
        logging.warning(
            "Case definition of "
            + case_dict[CASE_NAME]
            + " faulty at genset_fixed_capacity. Value can only be False, float or None"
        )

    # ------------Rectifier AC DC------------#
    if case_dict[RECTIFIER_AC_DC_FIXED_CAPACITY] == None:
        rectifier = None

    elif case_dict[RECTIFIER_AC_DC_FIXED_CAPACITY] is False:
        rectifier = generate.rectifier_oem(
            micro_grid_system, bus_electricity_ac, bus_electricity_dc, experiment
        )

    elif isinstance(case_dict[RECTIFIER_AC_DC_FIXED_CAPACITY], float):
        rectifier = generate.rectifier_fix(
            micro_grid_system,
            bus_electricity_ac,
            bus_electricity_dc,
            experiment,
            case_dict[RECTIFIER_AC_DC_FIXED_CAPACITY],
        )

    else:
        logging.warning(
            "Case definition of "
            + case_dict[CASE_NAME]
            + " faulty at rectifier_ac_dc_capacity_. Value can only be False, float or None"
        )

    # ------------Inverter DC AC------------#
    if case_dict[INVERTER_DC_AC_FIXED_CAPACITY] == None:
        inverter = None

    elif case_dict[INVERTER_DC_AC_FIXED_CAPACITY] is False:
        inverter = generate.inverter_dc_ac_oem(
            micro_grid_system, bus_electricity_ac, bus_electricity_dc, experiment
        )

    elif isinstance(case_dict[INVERTER_DC_AC_FIXED_CAPACITY], float):
        inverter = generate.inverter_dc_ac_fix(
            micro_grid_system,
            bus_electricity_ac,
            bus_electricity_dc,
            experiment,
            case_dict[INVERTER_DC_AC_FIXED_CAPACITY],
        )

    else:
        logging.warning(
            "Case definition of "
            + case_dict[CASE_NAME]
            + " faulty at inverter_dc_ac_capacity. Value can only be False, float or None"
        )

    ###################################
    ## Global sinks / sources         #
    ###################################

    # ------------Excess sink------------#
    generate.excess(micro_grid_system, bus_electricity_ac, bus_electricity_dc)

    # ------------Optional: Shortage source------------#
    if case_dict[ALLOW_SHORTAGE] is True:
        source_shortage = generate.shortage(
            micro_grid_system,
            bus_electricity_ac,
            bus_electricity_dc,
            experiment,
            case_dict,
        )  # changed order
    else:
        source_shortage = None

    logging.debug("Create oemof model based on created components and busses.")
    model = solph.Model(micro_grid_system)

    # ------------Stability constraint------------#
    if case_dict[STABILITY_CONSTRAINT] is False:
        pass
    elif case_dict[STABILITY_CONSTRAINT] == SHARE_BACKUP:
        logging.info("Added constraint: Stability through backup.")
        constraints_custom.backup(
            model,
            case_dict,
            experiment=experiment,
            storage=storage,
            sink_demand=sink_demand_ac,
            genset=genset,
            pcc_consumption=pointofcoupling_consumption,
            source_shortage=source_shortage,
            el_bus_ac=bus_electricity_ac,
            el_bus_dc=bus_electricity_dc,
        )
    elif case_dict[STABILITY_CONSTRAINT] == SHARE_USAGE:
        logging.info("Added constraint: Stability though actual generation.")
        constraints_custom.usage(
            model,
            case_dict,
            experiment=experiment,
            storage=storage,
            sink_demand=sink_demand_ac,
            genset=genset,
            pcc_consumption=pointofcoupling_consumption,
            source_shortage=source_shortage,
            el_bus=bus_electricity_ac,
        )
    elif case_dict[STABILITY_CONSTRAINT] == SHARE_HYBRID:
        logging.info(
            "Added constraint: Stability though actual generation of diesel generators and backup through batteries."
        )
        constraints_custom.hybrid(
            model,
            case_dict,
            experiment=experiment,
            storage=storage,
            sink_demand=sink_demand_ac,
            genset=genset,
            pcc_consumption=pointofcoupling_consumption,
            source_shortage=source_shortage,
            el_bus_ac=bus_electricity_ac,
            el_bus_dc=bus_electricity_dc,
        )
    elif case_dict[STABILITY_CONSTRAINT] == CRITICAL:
        # TODO: add the function to make the stability constraint favor critical demand over demand
        pass
        # constraints_custom.critical(
        #     model,
        # )
    else:
        logging.warning(
            "Case definition of "
            + case_dict[CASE_NAME]
            + " faulty at stability_constraint. Value can only be False, float or None"
        )

    # ------------Renewable share constraint------------#
    if case_dict[RENEWABLE_SHARE_CONSTRAINT] is False:
        pass
    elif case_dict[RENEWABLE_SHARE_CONSTRAINT] is True:
        logging.info("Adding constraint: Renewable share.")
        constraints_custom.share(
            model,
            case_dict,
            experiment,
            genset=genset,
            pcc_consumption=pointofcoupling_consumption,
            solar_plant=solar_plant,
            wind_plant=wind_plant,
            el_bus_ac=bus_electricity_ac,
            el_bus_dc=bus_electricity_dc,
        )
    else:
        logging.warning(
            "Case definition of "
            + case_dict[CASE_NAME]
            + " faulty at renewable_share_constraint. Value can only be True or False"
        )

    # ------------Force charge from maingrid------------#
    if case_dict[FORCE_CHARGE_FROM_MAINGRID] is False:
        pass
    elif case_dict[FORCE_CHARGE_FROM_MAINGRID] is True:
        logging.info("Added constraint: Forcing charge from main grid.")
        constraints_custom.forced_charge(
            model, case_dict, bus_electricity_dc, storage, experiment
        )
    else:
        logging.warning(
            "Case definition of "
            + case_dict[CASE_NAME]
            + " faulty at force_charge_from_maingrid. Value can only be True or False"
        )

    # ------------Allow discharge only at maingrid blackout------------#
    if case_dict[DISCHARGE_ONLY_WHEN_BLACKOUT] is False:
        pass
    elif case_dict[DISCHARGE_ONLY_WHEN_BLACKOUT] is True:
        logging.info("Added constraint: Allowing discharge only at blackout times.")
        constraints_custom.discharge_only_at_blackout(
            model, case_dict, bus_electricity_dc, storage, experiment
        )
    else:
        logging.warning(
            "Case definition of "
            + case_dict[CASE_NAME]
            + " faulty at discharge_only_when_blackout. Value can only be True or False"
        )

    # ------------Allow inverter use only at maingrid blackout------------#
    if case_dict[ENABLE_INVERTER_ONLY_AT_BLACKOUT] is False:
        pass
    elif case_dict[ENABLE_INVERTER_ONLY_AT_BLACKOUT] is True:
        logging.info("Added constraint: Allowing inverter use only at blackout times.")
        constraints_custom.inverter_only_at_blackout(
            model, case_dict, bus_electricity_dc, inverter, experiment
        )
    else:
        logging.warning(
            "Case definition of "
            + case_dict[CASE_NAME]
            + " faulty at enable_inverter_at_backout. Value can only be True or False"
        )

    """
    # ------------Allow shortage only for certain percentage of demand in a timestep------------#
    if case_dict['allow_shortage'] is True:
        if bus_electricity_ac != None:
            shortage_constraints.timestep(model, case_dict, experiment, sink_demand_ac, 
                                          source_shortage, bus_electricity_ac)
        if bus_electricity_dc != None:
            shortage_constraints.timestep(model, case_dict, experiment, sink_demand_dc, 
                                          source_shortage, bus_electricity_dc)
    """
    return micro_grid_system, model


def simulate(experiment, micro_grid_system, model, file_name):
    """
    Simulates the optimization problem using the given model and experiment's settings

    Parameters
    ----------
    experiment: dict
        Contains general settings for the experiment

    micro_grid_system: oemof.solph.network.EnergySystem
        Energy system for oemof optimization

    model: oemof.solph.models.Model
        Model used for the oemof optimization

    file_name: str
        Name used for saving the simulation's result

    Returns
    -------
    micro_grid_system: oemof.solph.network.EnergySystem
        Model for the optimization with integrated results

    """
    logging.info("Simulating...")
    model.solve(
        solver=experiment[SOLVER],
        solve_kwargs={
            "tee": experiment[SOLVER_VERBOSE]
        },  # if tee_switch is true solver messages will be displayed
        cmdline_options={
            experiment[CMDLINE_OPTION]: str(experiment[CMDLINE_OPTION_VALUE])
        },
    )  # ratioGap allowedGap mipgap
    logging.debug("Problem solved")

    if experiment["save_lp_file"] is True:
        logging.debug("Saving lp-file to folder.")
        model.write(
            experiment[OUTPUT_FOLDER] + "/lp_files/model_" + file_name + ".lp",
            io_options={SYMBOLIC_SOLVER_LABELS: True},
        )

    # add results to the energy system to make it possible to store them.
    micro_grid_system.results[MAIN] = processing.results(model)
    micro_grid_system.results[META] = processing.meta_results(model)
    return micro_grid_system


def store_results(micro_grid_system, file_name, output_folder):
    """
    Stores the results of the oemof simulation to an `.oemof` file.
    Output folder and name are defined by the user in the input sheet.

    Parameters
    ----------
    micro_grid_system: oemof.solph.network.EnergySystem
        Energy system for oemof optimization

    file_name: str
        Name used for saving the simulation's result

    output_folder: str
        Path to the output folder

    Returns
    -------
    micro_grid_system: oemof.solph.network.EnergySystem
    """
    # store energy system with results
    micro_grid_system.dump(
        dpath=output_folder + OEMOF_FOLDER, filename=file_name + ".oemof"
    )
    logging.debug(
        "Stored results in " + output_folder + OEMOF_FOLDER + "/" + file_name + ".oemof"
    )
    return micro_grid_system


def load_oemof_results(output_folder, file_name):
    """
    Loads simulation results stored in an `.oemof` file.

    Parameters
    ----------
    output_folder: str
        Path to the output folder

    file_name: str
        Name used for saving the simulation's result

    Returns
    -------
    micro_grid_system: oemof.solph.network.EnergySystem
    Model for the optimization with integrated results

    """
    logging.debug("Restore the energy system and the results.")
    micro_grid_system = solph.EnergySystem()
    micro_grid_system.restore(
        dpath=output_folder + OEMOF_FOLDER, filename=file_name + ".oemof"
    )
    return micro_grid_system
