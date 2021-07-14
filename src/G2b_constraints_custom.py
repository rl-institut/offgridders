"""
For defining custom constraints of the micro grid solutions
"""
import pyomo.environ as po
import logging
import pandas as pd
import oemof.solph as solph
from src.constants import (
    SHORTAGE_LIMIT,
    NUMBER_OF_EQUAL_GENERATORS,
    GENSET_FIXED_CAPACITY,
    PCC_CONSUMPTION_FIXED_CAPACITY,
    ALLOW_SHORTAGE,
    GRID_AVAILABILITY,
    STORAGE_FIXED_CAPACITY,
    STORAGE_CAPACITY_MIN,
    STORAGE_CRATE_DISCHARGE,
    STORAGE_EFFICIENCY_DISCHARGE,
    INVERTER_DC_AC_EFFICIENCY,
    STORAGE_FIXED_POWER,
    STABILITY_CONSTRAINT,
    DEMAND,
    STORED_CAPACITY,
    CAPACITY_PCOUPLING_KW,
    CAPACITY_GENSET_KW,
    DEMAND_SHORTAGE,
    CAPACITY_STORAGE_KWH,
    PEAK_DEMAND,
    STORAGE_SOC_MIN,
    CONSUMPTION_MAIN_GRID_MG_SIDE,
    GENSET_GENERATION,
    PEAK_DEMAND_AC,
    STORAGE_DISCHARGE,
    COMMENTS,
    MAINGRID_RENEWABLE_SHARE,
    MIN_RENEWABLE_SHARE,
    RENEWABLE_SHARE_CONSTRAINT,
    RES_SHARE,
    STORAGE_CRATE_CHARGE,
    STORAGE_SOC_MAX,
    FORCE_CHARGE_FROM_MAINGRID,
    STORAGE_CHARGE_DC,
    DISCHARGE_ONLY_WHEN_BLACKOUT,
    STORAGE_DISCHARGE_DC,
    INVERTER_DC_AC_FIXED_CAPACITY,
    ENABLE_INVERTER_ONLY_AT_BLACKOUT,
    INVERTER_INPUT,
    CAPACITY_INVERTER_DC_AC_KW,
    SHORTAGE_MAX_TIMESTEP,
)


def backup(
    model,
    case_dict,
    experiment,
    storage,
    sink_demand,
    genset,
    pcc_consumption,
    source_shortage,
    el_bus_ac,
    el_bus_dc,
):
    stability_limit = experiment[SHORTAGE_LIMIT]
    ## ------- Get CAP genset ------- #
    CAP_genset = 0
    if case_dict[GENSET_FIXED_CAPACITY] != None:
        if case_dict[GENSET_FIXED_CAPACITY] is False:
            for number in range(1, case_dict[NUMBER_OF_EQUAL_GENERATORS] + 1):
                CAP_genset += model.InvestmentFlow.invest[genset[number], el_bus_ac]
        elif isinstance(case_dict[GENSET_FIXED_CAPACITY], float):
            for number in range(1, case_dict[NUMBER_OF_EQUAL_GENERATORS] + 1):
                CAP_genset += model.flows[genset[number], el_bus_ac].nominal_value

    ## ------- Get CAP PCC ------- #
    CAP_pcc = 0
    if case_dict[PCC_CONSUMPTION_FIXED_CAPACITY] != None:
        if case_dict[PCC_CONSUMPTION_FIXED_CAPACITY] is False:
            CAP_pcc += model.InvestmentFlow.invest[pcc_consumption, el_bus_ac]
        elif isinstance(case_dict[PCC_CONSUMPTION_FIXED_CAPACITY], float):
            CAP_pcc += case_dict[
                PCC_CONSUMPTION_FIXED_CAPACITY
            ]  # this didnt work - model.flows[pcc_consumption, el_bus_ac].nominal_value

    def stability_rule_capacity(model, t):
        expr = CAP_genset
        ## ------- Get demand at t ------- #
        demand = model.flow[el_bus_ac, sink_demand, t]
        expr += -stability_limit * demand
        ## ------- Get shortage at t------- #
        if case_dict[ALLOW_SHORTAGE] is True:
            shortage = model.flow[source_shortage, el_bus_ac, t]
            # todo is this correct?
            expr += +stability_limit * shortage
        ##---------Grid consumption t-------#
        # this should not be actual consumption but possible one  - like grid_availability[t]*pcc_consumption_cap
        if case_dict[PCC_CONSUMPTION_FIXED_CAPACITY] != None:
            expr += CAP_pcc * experiment[GRID_AVAILABILITY][t]

        ## ------- Get stored capacity storage at t------- #
        if case_dict[STORAGE_FIXED_CAPACITY] != None:
            stored_electricity = 0
            if case_dict[STORAGE_FIXED_CAPACITY] is False:  # Storage subject to OEM
                stored_electricity += (
                    model.GenericInvestmentStorageBlock.storage_content[storage, t]
                    - experiment[STORAGE_CAPACITY_MIN]
                    * model.GenericInvestmentStorageBlock.invest[storage]
                )
            elif isinstance(
                case_dict[STORAGE_FIXED_CAPACITY], float
            ):  # Fixed storage subject to dispatch
                stored_electricity += (
                    model.GenericStorageBlock.storage_content[storage, t]
                    - experiment[STORAGE_CAPACITY_MIN] * storage.nominal_capacity
                )
            else:
                logging.warning(
                    "Error: 'storage_fixed_capacity' can only be None, False or float."
                )
            expr += (
                stored_electricity
                * experiment[STORAGE_CRATE_DISCHARGE]
                * experiment[STORAGE_EFFICIENCY_DISCHARGE]
                * experiment[INVERTER_DC_AC_EFFICIENCY]
            )
        return expr >= 0

    def stability_rule_power(model, t):
        expr = CAP_genset
        ## ------- Get demand at t ------- #
        demand = model.flow[el_bus_ac, sink_demand, t]
        expr += -stability_limit * demand
        ## ------- Get shortage at t------- #
        if case_dict[ALLOW_SHORTAGE] is True:
            shortage = model.flow[source_shortage, el_bus_ac, t]
            # todo is this correct?
            expr += +stability_limit * shortage
        ##---------Grid consumption t-------#
        # this should not be actual consumption but possible one  - like grid_availability[t]*pcc_consumption_cap
        if case_dict[PCC_CONSUMPTION_FIXED_CAPACITY] != None:
            expr += CAP_pcc * experiment[GRID_AVAILABILITY][t]

        ## ------- Get power of storage ------- #
        if case_dict[STORAGE_FIXED_POWER] != None:
            storage_power = 0
            if case_dict[STORAGE_FIXED_CAPACITY] is False:
                storage_power += model.InvestmentFlow.invest[storage, el_bus_dc]
            elif isinstance(case_dict[STORAGE_FIXED_CAPACITY], float):
                storage_power += case_dict[STORAGE_FIXED_POWER]
            else:
                logging.warning(
                    "Error: 'storage_fixed_power' can only be None, False or float."
                )

            expr += storage_power * experiment[INVERTER_DC_AC_EFFICIENCY]
        return expr >= 0

    model.stability_constraint = po.Constraint(
        model.TIMESTEPS, rule=stability_rule_capacity
    )
    model.stability_constraint_power = po.Constraint(
        model.TIMESTEPS, rule=stability_rule_power
    )
    return model


def backup_test(case_dict, oemof_results, experiment, e_flows_df):
    """
    Testing simulation results for adherance to above defined stability criterion
    """
    if case_dict[STABILITY_CONSTRAINT] != False:
        demand_profile = e_flows_df[DEMAND]

        if STORED_CAPACITY in e_flows_df.columns:
            stored_electricity = e_flows_df[STORED_CAPACITY]
        else:
            stored_electricity = pd.Series(
                [0 for t in demand_profile.index], index=demand_profile.index
            )

        if GRID_AVAILABILITY in e_flows_df.columns:
            pcc_capacity = (
                oemof_results[CAPACITY_PCOUPLING_KW] * e_flows_df[GRID_AVAILABILITY]
            )
        else:
            pcc_capacity = pd.Series(
                [0 for t in demand_profile.index], index=demand_profile.index
            )

        genset_capacity = oemof_results[CAPACITY_GENSET_KW]

        if case_dict[ALLOW_SHORTAGE] is True:
            shortage = e_flows_df[DEMAND_SHORTAGE]
        else:
            shortage = pd.Series(
                [0 for t in demand_profile.index], index=demand_profile.index
            )

        boolean_test = [
            genset_capacity
            + (
                stored_electricity[t]
                - oemof_results[CAPACITY_STORAGE_KWH] * experiment[STORAGE_CAPACITY_MIN]
            )
            * experiment[STORAGE_CRATE_DISCHARGE]
            * experiment[STORAGE_EFFICIENCY_DISCHARGE]
            * experiment[INVERTER_DC_AC_EFFICIENCY]
            + pcc_capacity[t]
            >= experiment[SHORTAGE_LIMIT] * (demand_profile[t] - shortage[t])
            for t in range(0, len(demand_profile.index))
        ]

        if all(boolean_test) is True:
            logging.debug("Stability criterion is fullfilled.")
        else:
            ratio = pd.Series(
                [
                    (
                        genset_capacity
                        + (
                            stored_electricity[t]
                            - oemof_results[CAPACITY_STORAGE_KWH]
                            * experiment[STORAGE_CAPACITY_MIN]
                        )
                        * experiment[STORAGE_CRATE_DISCHARGE]
                        * experiment[STORAGE_EFFICIENCY_DISCHARGE]
                        * experiment[INVERTER_DC_AC_EFFICIENCY]
                        + pcc_capacity[t]
                        - experiment[SHORTAGE_LIMIT] * (demand_profile[t] - shortage[t])
                    )
                    / (experiment[PEAK_DEMAND])
                    for t in range(0, len(demand_profile.index))
                ],
                index=demand_profile.index,
            )
            ratio_below_zero = ratio.clip_upper(0)
            test_warning(ratio_below_zero, oemof_results, boolean_test)
    else:
        pass


def hybrid(
    model,
    case_dict,
    experiment,
    storage,
    sink_demand,
    genset,
    pcc_consumption,
    source_shortage,
    el_bus_ac,
    el_bus_dc,
):

    stability_limit = experiment[SHORTAGE_LIMIT]

    def stability_rule_capacity(model, t):
        expr = 0
        ## ------- Get demand at t ------- #
        demand = model.flow[el_bus_ac, sink_demand, t]
        expr += -stability_limit * demand

        ## ------- Get shortage at t------- #
        if case_dict[ALLOW_SHORTAGE] is True:
            shortage = model.flow[source_shortage, el_bus_ac, t]
            expr += +stability_limit * shortage

        ## ------- Generation Diesel ------- #
        if case_dict[GENSET_FIXED_CAPACITY] != None:
            for number in range(1, case_dict[NUMBER_OF_EQUAL_GENERATORS] + 1):
                expr += model.flow[genset[number], el_bus_ac, t]

        ##---------Grid consumption t-------#
        if case_dict[PCC_CONSUMPTION_FIXED_CAPACITY] != None:
            expr += model.flow[pcc_consumption, el_bus_ac, t]

        ## ------- Get stored capacity storage at t------- #
        if case_dict[STORAGE_FIXED_CAPACITY] != None:
            stored_electricity = 0
            if case_dict[STORAGE_FIXED_CAPACITY] is False:  # Storage subject to OEM
                stored_electricity += (
                    model.GenericInvestmentStorageBlock.storage_content[storage, t]
                    - experiment[STORAGE_SOC_MIN]
                    * model.GenericInvestmentStorageBlock.invest[storage]
                )
            elif isinstance(
                case_dict[STORAGE_FIXED_CAPACITY], float
            ):  # Fixed storage subject to dispatch
                stored_electricity += (
                    model.GenericStorageBlock.storage_content[storage, t]
                    - experiment[STORAGE_SOC_MIN] * storage.nominal_capacity
                )
            else:
                logging.warning(
                    "Error: 'storage_fixed_capacity' can only be None, False or float."
                )
            expr += (
                stored_electricity
                * experiment[STORAGE_CRATE_DISCHARGE]
                * experiment[STORAGE_EFFICIENCY_DISCHARGE]
                * experiment[INVERTER_DC_AC_EFFICIENCY]
            )
        return expr >= 0

    def stability_rule_power(model, t):
        expr = 0
        ## ------- Get demand at t ------- #
        demand = model.flow[el_bus_ac, sink_demand, t]
        expr += -stability_limit * demand

        ## ------- Get shortage at t------- #
        if case_dict[ALLOW_SHORTAGE] is True:
            shortage = model.flow[source_shortage, el_bus_ac, t]
            expr += +stability_limit * shortage

        ## ------- Generation Diesel ------- #
        if case_dict[GENSET_FIXED_CAPACITY] != None:
            for number in range(1, case_dict[NUMBER_OF_EQUAL_GENERATORS] + 1):
                expr += model.flow[genset[number], el_bus_ac, t]

        ##---------Grid consumption t-------#
        if case_dict[PCC_CONSUMPTION_FIXED_CAPACITY] != None:
            expr += model.flow[pcc_consumption, el_bus_ac, t]

        ## ------- Get power of storage ------- #
        if case_dict[STORAGE_FIXED_POWER] != None:
            storage_power = 0
            if case_dict[STORAGE_FIXED_CAPACITY] is False:
                storage_power += model.InvestmentFlow.invest[storage, el_bus_dc]
            elif isinstance(case_dict[STORAGE_FIXED_CAPACITY], float):
                storage_power += case_dict[STORAGE_FIXED_POWER]
            else:
                logging.warning(
                    "Error: 'storage_fixed_power' can only be None, False or float."
                )

            expr += storage_power * experiment[INVERTER_DC_AC_EFFICIENCY]
        return expr >= 0

    model.stability_constraint_capacity = po.Constraint(
        model.TIMESTEPS, rule=stability_rule_capacity
    )
    model.stability_constraint_power = po.Constraint(
        model.TIMESTEPS, rule=stability_rule_power
    )
    return model


def hybrid_test(case_dict, oemof_results, experiment, e_flows_df):
    """
    Testing simulation results for adherance to above defined stability criterion
    #todo actually this does not test the stability_share_power criterion, which includes the storage power!
    """
    if case_dict[STABILITY_CONSTRAINT] != False:
        demand_profile = e_flows_df[DEMAND]

        if case_dict[ALLOW_SHORTAGE] is True:
            shortage = e_flows_df[DEMAND_SHORTAGE]
        else:
            shortage = pd.Series(
                [0 for t in demand_profile.index], index=demand_profile.index
            )

        if STORED_CAPACITY in e_flows_df.columns:
            stored_electricity = e_flows_df[STORED_CAPACITY]
        else:
            stored_electricity = pd.Series(
                [0 for t in demand_profile.index], index=demand_profile.index
            )

        if CONSUMPTION_MAIN_GRID_MG_SIDE in e_flows_df.columns:
            pcc_consumption = e_flows_df[CONSUMPTION_MAIN_GRID_MG_SIDE]
        else:
            pcc_consumption = pd.Series(
                [0 for t in demand_profile.index], index=demand_profile.index
            )

        if GENSET_GENERATION in e_flows_df.columns:
            genset_generation = e_flows_df[GENSET_GENERATION]
        else:
            genset_generation = pd.Series(
                [0 for t in demand_profile.index], index=demand_profile.index
            )

        boolean_test = [
            genset_generation[t]
            + (
                stored_electricity[t]
                - oemof_results[CAPACITY_STORAGE_KWH] * experiment[STORAGE_SOC_MIN]
            )
            * experiment[STORAGE_CRATE_DISCHARGE]
            * experiment[STORAGE_EFFICIENCY_DISCHARGE]
            * experiment[INVERTER_DC_AC_EFFICIENCY]
            + pcc_consumption[t]
            >= experiment[SHORTAGE_LIMIT] * (demand_profile[t] - shortage[t])
            for t in range(0, len(demand_profile.index))
        ]

        if all(boolean_test) is True:
            logging.debug("Stability criterion is fullfilled.")
        else:
            ratio = pd.Series(
                [
                    (
                        genset_generation[t]
                        + (
                            stored_electricity[t]
                            - oemof_results[CAPACITY_STORAGE_KWH]
                            * experiment[STORAGE_SOC_MIN]
                        )
                        * experiment[STORAGE_CRATE_DISCHARGE]
                        * experiment[STORAGE_EFFICIENCY_DISCHARGE]
                        * experiment[INVERTER_DC_AC_EFFICIENCY]
                        + pcc_consumption[t]
                        - experiment[SHORTAGE_LIMIT] * (demand_profile[t] - shortage[t])
                    )
                    / (experiment[PEAK_DEMAND_AC])
                    for t in range(0, len(demand_profile.index))
                ],
                index=demand_profile.index,
            )
            ratio_below_zero = ratio.clip_upper(0)
            test_warning(ratio_below_zero, oemof_results, boolean_test)

    else:
        pass

    return


def usage(
    model,
    case_dict,
    experiment,
    storage,
    sink_demand,
    genset,
    pcc_consumption,
    source_shortage,
    el_bus,
):

    stability_limit = experiment[SHORTAGE_LIMIT]

    def stability_rule(model, t):
        expr = 0
        ## ------- Get demand at t ------- #
        demand = model.flow[el_bus, sink_demand, t]

        expr += -stability_limit * demand

        ## ------- Get shortage at t------- #
        if case_dict[ALLOW_SHORTAGE] is True:
            shortage = model.flow[source_shortage, el_bus, t]
            expr += stability_limit * shortage

        ## ------- Generation Diesel ------- #
        if case_dict[GENSET_FIXED_CAPACITY] != None:
            for number in range(1, case_dict[NUMBER_OF_EQUAL_GENERATORS] + 1):
                expr += model.flow[genset[number], el_bus, t]

        ##---------Grid consumption t-------#
        if case_dict[PCC_CONSUMPTION_FIXED_CAPACITY] != None:
            expr += model.flow[pcc_consumption, el_bus, t]

        ## ------- Get discharge storage at t------- #
        if case_dict[STORAGE_FIXED_CAPACITY] != None:
            expr += (
                model.flow[storage, el_bus, t] * experiment[INVERTER_DC_AC_EFFICIENCY]
            )
        return expr >= 0

    model.stability_constraint = po.Constraint(model.TIMESTEPS, rule=stability_rule)

    return model


def usage_test(case_dict, oemof_results, experiment, e_flows_df):
    """
    Testing simulation results for adherance to above defined stability criterion
    """
    if case_dict[STABILITY_CONSTRAINT] != False:
        demand_profile = e_flows_df[DEMAND]

        if case_dict[ALLOW_SHORTAGE] is True:
            shortage = e_flows_df[DEMAND_SHORTAGE]
        else:
            shortage = pd.Series(
                [0 for t in demand_profile.index], index=demand_profile.index
            )

        if STORAGE_DISCHARGE in e_flows_df.columns:
            storage_discharge = e_flows_df[STORAGE_DISCHARGE]
        else:
            storage_discharge = pd.Series(
                [0 for t in demand_profile.index], index=demand_profile.index
            )

        if CONSUMPTION_MAIN_GRID_MG_SIDE in e_flows_df.columns:
            pcc_feedin = e_flows_df[CONSUMPTION_MAIN_GRID_MG_SIDE]
        else:
            pcc_feedin = pd.Series(
                [0 for t in demand_profile.index], index=demand_profile.index
            )

        if GENSET_GENERATION in e_flows_df.columns:
            genset_generation = e_flows_df[GENSET_GENERATION]
        else:
            genset_generation = pd.Series(
                [0 for t in demand_profile.index], index=demand_profile.index
            )

        boolean_test = [
            genset_generation[t]
            + storage_discharge[t] * experiment[INVERTER_DC_AC_EFFICIENCY]
            + pcc_feedin[t]
            >= experiment[SHORTAGE_LIMIT] * (demand_profile[t] - shortage[t])
            for t in range(0, len(demand_profile.index))
        ]

        if all(boolean_test) is True:
            logging.debug("Stability criterion is fullfilled.")
        else:
            ratio = pd.Series(
                [
                    (
                        genset_generation[t]
                        + storage_discharge[t] * experiment[INVERTER_DC_AC_EFFICIENCY]
                        + pcc_feedin[t]
                        - experiment[SHORTAGE_LIMIT] * (demand_profile[t] - shortage[t])
                    )
                    / (experiment[PEAK_DEMAND])
                    for t in range(0, len(demand_profile.index))
                ],
                index=demand_profile.index,
            )
            ratio_below_zero = ratio.clip_upper(0)
            test_warning(ratio_below_zero, oemof_results, boolean_test)
    else:
        pass

    return


def test_warning(ratio_below_zero, oemof_results, boolean_test):
    if abs(ratio_below_zero.values.min()) < 10 ** (-6):
        logging.warning(
            "Stability criterion is strictly not fullfilled, but deviation is less then e6."
        )
    else:
        logging.warning("ATTENTION: Stability criterion NOT fullfilled!")
        logging.warning(
            "Number of timesteps not meeting criteria: " + str(sum(boolean_test))
        )
        logging.warning(
            "Deviation from stability criterion: "
            + str(ratio_below_zero.values.mean())
            + "(mean) / "
            + str(ratio_below_zero.values.min())
            + "(max)."
        )
        oemof_results.update(
            {
                COMMENTS: oemof_results[COMMENTS]
                + "Stability criterion not fullfilled (max deviation "
                + str(round(100 * ratio_below_zero.values.min(), 4))
                + "%). "
            }
        )
    return


def share(
    model,
    case_dict,
    experiment,
    genset,
    pcc_consumption,
    solar_plant,
    wind_plant,
    el_bus_ac,
    el_bus_dc,
):  # wind_plant
    """
    Resulting in an energy system adhering to a minimal renewable factor

      .. math::
            minimal renewable factor <= 1 - (fossil fuelled generation + main grid consumption * (1-main grid renewable factor)) / total_demand

    Parameters
    - - - - - - - -
    model: oemof.solph.model
        Model to which constraint is added. Has to contain:
        - Transformer (genset)
        - optional: pcc

    experiment: dict with entries...
        - 'min_res_share': Share of demand that can be met by fossil fuelled generation (genset, from main grid) to meet minimal renewable share
        - optional: 'main_grid_renewable_share': Share of main grid electricity that is generated renewably

    genset: currently single object of class oemof.solph.network.Transformer
        To get available capacity genset
        Can either be an investment object or have a nominal capacity

    pcc_consumption: currently single object of class oemof.solph.network.Transformer
        Connecting main grid bus to electricity bus of micro grid (consumption)

    el_bus: object of class oemof.solph.network.Bus
        For accessing flow-parameters
    """

    def renewable_share_rule(model):
        fossil_generation = 0
        total_generation = 0

        if genset is not None:
            for number in range(1, case_dict[NUMBER_OF_EQUAL_GENERATORS] + 1):
                genset_generation_kWh = sum(model.flow[genset[number], el_bus_ac, :])
                total_generation += genset_generation_kWh
                fossil_generation += genset_generation_kWh

        if pcc_consumption is not None:
            pcc_consumption_kWh = sum(model.flow[pcc_consumption, el_bus_ac, :])
            total_generation += pcc_consumption_kWh
            fossil_generation += pcc_consumption_kWh * (
                1 - experiment[MAINGRID_RENEWABLE_SHARE]
            )

        if solar_plant is not None:
            solar_plant_generation = sum(model.flow[solar_plant, el_bus_dc, :])
            total_generation += solar_plant_generation

        if wind_plant is not None:
            wind_plant_generation = sum(model.flow[wind_plant, el_bus_ac, :])
            total_generation += wind_plant_generation

        expr = (
            fossil_generation - (1 - experiment[MIN_RENEWABLE_SHARE]) * total_generation
        )
        return expr <= 0

    model.renewable_share_constraint = po.Constraint(rule=renewable_share_rule)

    return model


def share_test(case_dict, oemof_results, experiment):
    """
    Testing simulation results for adherance to above defined stability criterion
    """
    if case_dict[RENEWABLE_SHARE_CONSTRAINT] is True:
        boolean_test = oemof_results[RES_SHARE] >= experiment[MIN_RENEWABLE_SHARE]
        if boolean_test is False:
            deviation = (
                experiment[MIN_RENEWABLE_SHARE] - oemof_results[RES_SHARE]
            ) / experiment[MIN_RENEWABLE_SHARE]
            if abs(deviation) < 10 ** (-6):
                logging.warning(
                    "Minimal renewable share criterion strictly not fullfilled, but deviation is less then e6."
                )
            else:
                logging.warning(
                    "ATTENTION: Minimal renewable share criterion NOT fullfilled!"
                )
                oemof_results.update(
                    {
                        COMMENTS: oemof_results[COMMENTS]
                        + "Renewable share criterion not fullfilled. "
                    }
                )
        else:
            logging.debug("Minimal renewable share is fullfilled.")
    else:
        pass

    return


def forced_charge(model, case_dict, el_bus_dc, storage, experiment):
    ## ------- Get CAP Storage ------- #
    CAP_storage = 0
    if case_dict[STORAGE_FIXED_CAPACITY] != None:
        if case_dict[STORAGE_FIXED_CAPACITY] is False:
            CAP_storage += model.GenericInvestmentStorageBlock.invest[storage]
        elif isinstance(case_dict[STORAGE_FIXED_CAPACITY], float):
            CAP_storage += storage.nominal_capacity

    m = -experiment[STORAGE_CRATE_CHARGE] / (
        experiment[STORAGE_SOC_MAX] - experiment[STORAGE_SOC_MIN]
    )

    n = (
        experiment[STORAGE_CRATE_CHARGE]
        * CAP_storage
        * (
            1
            + experiment[STORAGE_SOC_MIN]
            / (experiment[STORAGE_SOC_MAX] - experiment[STORAGE_SOC_MIN])
        )
    )

    def linear_charge(model, t):
        ## ------- Get storaged electricity at t------- #
        stored_electricity = 0
        expr = 0
        if case_dict[STORAGE_FIXED_CAPACITY] != None:
            if case_dict[STORAGE_FIXED_CAPACITY] is False:  # Storage subject to OEM
                stored_electricity += model.GenericInvestmentStorageBlock.storage_content[
                    storage, t
                ]
            elif isinstance(
                case_dict[STORAGE_FIXED_CAPACITY], float
            ):  # Fixed storage subject to dispatch
                stored_electricity += model.GenericStorageBlock.storage_content[
                    storage, t
                ]

            # Linearization
            expr = m * stored_electricity + n  # * 0.99

            # Only apply linearization if no blackout occurs
            expr = expr * experiment[GRID_AVAILABILITY][t]

            # Actual charge
            expr += -model.flow[el_bus_dc, storage, t]
        return expr <= 0

    model.forced_charge_linear = po.Constraint(model.TIMESTEPS, rule=linear_charge)

    return model


def forced_charge_test(case_dict, oemof_results, experiment, e_flows_df):
    """
    Testing simulation results for adherance to above defined criterion
    """
    if case_dict[FORCE_CHARGE_FROM_MAINGRID] is True:
        boolean_test = [
            (
                experiment[STORAGE_CRATE_CHARGE]
                * oemof_results[CAPACITY_STORAGE_KWH]
                * (
                    1
                    + experiment[STORAGE_SOC_MIN]
                    / (experiment[STORAGE_SOC_MAX] - experiment[STORAGE_SOC_MIN])
                )
                + (oemof_results[CAPACITY_STORAGE_KWH] - e_flows_df[STORED_CAPACITY][t])
                / (experiment[STORAGE_SOC_MAX] - experiment[STORAGE_SOC_MIN])
            )
            * e_flows_df[GRID_AVAILABILITY][t]
            <= e_flows_df[STORAGE_CHARGE_DC][t]
            for t in range(0, len(e_flows_df.index))
        ]

        if all(boolean_test) is True:
            logging.debug(
                "Battery is always charged when grid availabile (linearized)."
            )
        else:

            deviation = pd.Series(
                [
                    (
                        experiment[STORAGE_CRATE_CHARGE]
                        * oemof_results[CAPACITY_STORAGE_KWH]
                        * (
                            1
                            + experiment[STORAGE_SOC_MIN]
                            / (
                                experiment[STORAGE_SOC_MAX]
                                - experiment[STORAGE_SOC_MIN]
                            )
                        )
                        + (
                            oemof_results[CAPACITY_STORAGE_KWH]
                            - e_flows_df[STORED_CAPACITY][t]
                        )
                        / (experiment[STORAGE_SOC_MAX] - experiment[STORAGE_SOC_MIN])
                    )
                    * e_flows_df[GRID_AVAILABILITY][t]
                    - e_flows_df[STORAGE_CHARGE_DC][t]
                    for t in range(0, len(e_flows_df.index))
                ],
                index=e_flows_df.index,
            )

            if max(deviation) < 10 ** (-6):
                logging.warning(
                    "Battery charge when grid available not as high as need be, but deviation is less then e6."
                )
            else:
                logging.warning(
                    "ATTENTION: Battery charge at grid availability does not take place adequately!"
                )
                oemof_results.update(
                    {
                        COMMENTS: oemof_results[COMMENTS]
                        + "Forced battery charge criterion not fullfilled. "
                    }
                )

    return


def discharge_only_at_blackout(model, case_dict, el_bus, storage, experiment):
    grid_inavailability = 1 - experiment[GRID_AVAILABILITY]

    def discharge_rule_upper(model, t):
        expr = 0
        stored_electricity = 0

        if case_dict[STORAGE_FIXED_CAPACITY] != None:
            # Battery discharge flow
            expr += model.flow[storage, el_bus, t]
            # Get stored electricity at t
            if case_dict[STORAGE_FIXED_CAPACITY] is False:  # Storage subject to OEM
                stored_electricity += model.GenericInvestmentStorageBlock.storage_content[
                    storage, t
                ]
            elif isinstance(
                case_dict[STORAGE_FIXED_CAPACITY], float
            ):  # Fixed storage subject to dispatch
                stored_electricity += model.GenericStorageBlock.storage_content[
                    storage, t
                ]

            # force discharge to zero when grid available
            expr += -stored_electricity * grid_inavailability[t]

        return expr <= 0

    model.discharge_only_at_blackout_constraint = po.Constraint(
        model.TIMESTEPS, rule=discharge_rule_upper
    )

    return model


def discharge_only_at_blackout_test(case_dict, oemof_results, e_flows_df):
    """
    Testing simulation results for adherance to above defined criterion
    """
    if (
        case_dict[DISCHARGE_ONLY_WHEN_BLACKOUT] is True
        and case_dict[STORAGE_FIXED_CAPACITY] != None
    ):
        boolean_test = [
            e_flows_df[STORAGE_DISCHARGE_DC][t]
            <= (1 - e_flows_df[GRID_AVAILABILITY][t]) * e_flows_df[STORED_CAPACITY][t]
            for t in range(0, len(e_flows_df.index))
        ]

        if all(boolean_test) is True:
            logging.debug("Battery only discharged when grid unavailable.")
        else:
            ratio = pd.Series(
                [
                    (
                        e_flows_df[STORAGE_DISCHARGE_DC][t]
                        - (1 - e_flows_df[GRID_AVAILABILITY][t])
                        * e_flows_df[STORED_CAPACITY][t]
                    )
                    for t in range(0, len(e_flows_df.index))
                ],
                index=e_flows_df.index,
            )

            if max(ratio) < 10 ** (-6):
                logging.warning(
                    "Battery discharge when grid available, but deviation is less then e6."
                )
            else:
                logging.warning("ATTENTION: Battery charge when grid available!")
                oemof_results.update(
                    {
                        COMMENTS: oemof_results[COMMENTS]
                        + "Limitation of battery discharge to blackout not fullfilled. "
                    }
                )

    return


def inverter_only_at_blackout(model, case_dict, el_bus, inverter, experiment):
    grid_inavailability = 1 - experiment[GRID_AVAILABILITY]

    ## ------- Get CAP inverter ------- #
    CAP_inverter = 0
    if case_dict[INVERTER_DC_AC_FIXED_CAPACITY] != None:
        if case_dict[INVERTER_DC_AC_FIXED_CAPACITY] is False:
            CAP_inverter += model.InvestmentFlow.invest[el_bus, inverter]
        elif isinstance(case_dict[INVERTER_DC_AC_FIXED_CAPACITY], float):
            CAP_inverter += model.flows[el_bus, inverter].nominal_value

    def inverter_rule_upper(model, t):
        # Inverter flow
        expr = 0
        if case_dict[INVERTER_DC_AC_FIXED_CAPACITY] != None:
            expr += model.flow[el_bus, inverter, t]
        # force discharge to zero when grid available
        expr += -CAP_inverter * grid_inavailability[t]
        return expr <= 0

    model.inverter_only_at_blackout = po.Constraint(
        model.TIMESTEPS, rule=inverter_rule_upper
    )

    return model


def inverter_only_at_blackout_test(case_dict, oemof_results, e_flows_df):
    """
    Testing simulation results for adherance to above defined criterion
    """

    if (
        case_dict[ENABLE_INVERTER_ONLY_AT_BLACKOUT] is True
        and case_dict[INVERTER_DC_AC_FIXED_CAPACITY] != None
    ):
        boolean_test = [
            e_flows_df[INVERTER_INPUT][t]
            <= (1 - e_flows_df[GRID_AVAILABILITY][t])
            * oemof_results[CAPACITY_INVERTER_DC_AC_KW]
            for t in range(0, len(e_flows_df.index))
        ]

        if all(boolean_test) is True:
            logging.debug("Battery only discharged when grid unavailable.")
        else:
            ratio = pd.Series(
                [
                    (
                        e_flows_df[INVERTER_INPUT][t]
                        - (1 - e_flows_df[GRID_AVAILABILITY][t])
                        * oemof_results[CAPACITY_INVERTER_DC_AC_KW]
                    )
                    for t in range(0, len(e_flows_df.index))
                ],
                index=e_flows_df.index,
            )

            if max(ratio) < 10 ** (-6):
                logging.warning(
                    "Inverter use when grid available, but deviation is less then e6."
                )
            else:
                logging.warning("ATTENTION: Inverter use when grid available!")
                oemof_results.update(
                    {
                        COMMENTS: oemof_results[COMMENTS]
                        + "Inverter use when grid available. "
                    }
                )

    return

# equate bi-directional transformer capacities
def constraint_equate_bidirectional_transformer_capacities(model, case_dict, bus_transformer_in, bus_transformer_out, transformer_in, transformer_out, name_transformer_in, name_transformer_out, factor = 1):
    CAP_inverter = 0 
    CAP_rectifier = 0
    if case_dict[name_transformer_in] != None and case_dict[name_transformer_out] != None:
        if case_dict[name_transformer_in] is False and case_dict[name_transformer_out] is False:
                CAP_inverter += model.InvestmentFlow.invest[bus_transformer_in, transformer_in]
                CAP_rectifier += model.InvestmentFlow.invest[bus_transformer_out, transformer_out]
    solph.constraints.equate_variables(model,CAP_rectifier, CAP_inverter, factor)

    return model


# todo shortage constraint / stbaility constraint only relates to AC bus
def timestep(model, case_dict, experiment, el_bus, sink_demand, source_shortage):
    def stability_per_timestep_rule(model, t):
        expr = 0
        ## ------- Get demand at t ------- #
        demand = model.flow[el_bus, sink_demand, t]
        expr += experiment[SHORTAGE_MAX_TIMESTEP] * demand
        ## ------- Get shortage at t------- #
        if case_dict["allow_shortage"] is True:
            expr += -model.flow[source_shortage, el_bus, t]

        return expr >= 0

    model.stability_constraint = po.Constraint(
        model.TIMESTEPS, rule=stability_per_timestep_rule
    )

    return model
