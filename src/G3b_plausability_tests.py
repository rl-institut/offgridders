import logging

from src.constants import (
    STORAGE_DISCHARGE,
    STORAGE_CHARGE,
    COMMENTS,
    DEMAND_SUPPLIED,
    DEMAND,
    DEMAND_AC,
    DEMAND_SHORTAGE,
    CONSUMPTION_FROM_MAIN_GRID,
    FEED_INTO_MAIN_GRID,
    GRID_AVAILABILITY,
    EXCESS_ELECTRICITY,
    CAPACITY_PCC,
)

"""
e_flows_df can include columns with titles...
'Demand'
'Demand shortage'
'Demand supplied'
'PV generation'
'Excess electricity'
'Consumption from main grid (MG side)'
'Feed into main grid (MG side)'
'Consumption from main grid (utility side)'
'Feed into main grid (utility side)'
'Storage discharge'
'Storage charge'
'Genset generation'
'Excess generation'
'PV generation'
'Grid availability'
"""


def run(oemof_results, e_flows_df):
    """
    Checking oemof calculations for plausability. The most obvious errors should be identified this way.
    Ideally, not a single error should be displayed or added to the oemof comments.
    Checks include:
    - storage charge <-> dicharge
    - Demand <-> supplied demand <-> shortage
    - feedin <-> consumption
    - grid availability <-> feedin to grid
    - grid availability <-> consumption from grid
    - excess <-> shortage
    - excess <-> feedin > pcc cap and excess <-> grid availability
    """
    charge_discharge(oemof_results, e_flows_df)
    demand_supply_shortage(oemof_results, e_flows_df)
    feedin_consumption(oemof_results, e_flows_df)
    gridavailability_consumption(oemof_results, e_flows_df)
    gridavailability_feedin(oemof_results, e_flows_df)
    excess_shortage(oemof_results, e_flows_df)
    excess_feedin(oemof_results, e_flows_df)
    return


def charge_discharge(oemof_results, e_flows_df):
    logging.debug("Plausibility test: Charge/Discharge")
    if STORAGE_DISCHARGE in e_flows_df.columns and STORAGE_CHARGE in e_flows_df.columns:
        boolean = True

        test = [
            (
                e_flows_df[STORAGE_DISCHARGE][t] != 0
                and e_flows_df[STORAGE_CHARGE][t] == 0
            )
            for t in e_flows_df.index
        ]

        if any(test) is False:
            boolean = False

        if boolean is False:
            logging.warning(
                "PLAUSABILITY TEST FAILED: Charge and discharge of batteries at the same time!"
            )
            oemof_results.update(
                {
                    COMMENTS: oemof_results[COMMENTS]
                    + "Charge and discharge of batteries at the same time. "
                }
            )
    return


def demand_supply_shortage(oemof_results, e_flows_df):
    logging.debug("Plausibility test: Demand/Supply/Shortage")
    if (
        (DEMAND_SUPPLIED in e_flows_df.columns)
        and (DEMAND_AC in e_flows_df.columns)
        and (DEMAND_SHORTAGE in e_flows_df.columns)
    ):

        boolean = True

        test = [
            (
                (
                    e_flows_df[DEMAND_SUPPLIED][t] == e_flows_df[DEMAND_AC][t]
                    and e_flows_df[DEMAND_SHORTAGE][t] == 0
                )
                or (
                    (
                        e_flows_df[DEMAND_SUPPLIED][t] != e_flows_df[DEMAND_AC][t]
                        and e_flows_df[DEMAND_SHORTAGE][t] != 0
                    )
                )
            )
            for t in e_flows_df.index
        ]

        if any(test) is False:
            boolean = False

        if boolean is False:
            logging.warning(
                "PLAUSABILITY TEST FAILED: Demand not fully supplied but no shortage!"
            )
            oemof_results.update(
                {
                    COMMENTS: oemof_results[COMMENTS]
                    + "Demand not fully supplied but no shortage. "
                }
            )

    return


def feedin_consumption(oemof_results, e_flows_df):
    logging.debug("Plausibility test: Feedin/Consumption")
    if (CONSUMPTION_FROM_MAIN_GRID in e_flows_df.columns) and (
        FEED_INTO_MAIN_GRID in e_flows_df.columns
    ):

        boolean = True

        test = [
            (
                e_flows_df[CONSUMPTION_FROM_MAIN_GRID][t] != 0
                and e_flows_df[FEED_INTO_MAIN_GRID][t] != 0
            )
            for t in e_flows_df.index
        ]

        if any(test) is False:
            boolean = False

        if boolean is False:
            logging.warning(
                "PLAUSABILITY TEST FAILED: Feedin to and consumption from national grid at the same time!"
            )
            oemof_results.update(
                {
                    COMMENTS: oemof_results[COMMENTS]
                    + "Feedin to and consumption from national grid at the same time. "
                }
            )

    return


def gridavailability_feedin(oemof_results, e_flows_df):
    logging.debug("Plausibility test: Grid availability/Feedin")
    if (CONSUMPTION_FROM_MAIN_GRID in e_flows_df.columns) and (
        FEED_INTO_MAIN_GRID in e_flows_df.columns
    ):

        boolean = True

        test = [
            (
                e_flows_df[FEED_INTO_MAIN_GRID][t] != 0
                and e_flows_df[GRID_AVAILABILITY][t] == 0
            )
            for t in e_flows_df.index
        ]

        if any(test) is False:
            boolean = False

        if boolean is False:
            logging.warning(
                "PLAUSABILITY TEST FAILED: Feedin to national grid during blackout!"
            )
            oemof_results.update(
                {
                    COMMENTS: oemof_results[COMMENTS]
                    + "Feedin to national grid during blackout. "
                }
            )

    return


def gridavailability_consumption(oemof_results, e_flows_df):
    logging.debug("Plausibility test: Grid availability consumption")
    if (CONSUMPTION_FROM_MAIN_GRID in e_flows_df.columns) and (
        GRID_AVAILABILITY in e_flows_df.columns
    ):

        boolean = True

        test = [
            (
                e_flows_df[CONSUMPTION_FROM_MAIN_GRID][t] != 0
                and e_flows_df[GRID_AVAILABILITY][t] == 0
            )
            for t in e_flows_df.index
        ]

        if any(test) is False:
            boolean = False

        if boolean is False:
            logging.warning(
                "PLAUSABILITY TEST FAILED: Consumption from national grid during blackout!"
            )
            oemof_results.update(
                {
                    COMMENTS: oemof_results[COMMENTS]
                    + "Consumption from national grid during blackout. "
                }
            )

    return


def excess_shortage(oemof_results, e_flows_df):
    logging.debug("Plausibility test: Excess/shortage")
    if (EXCESS_ELECTRICITY in e_flows_df.columns) and (
        DEMAND_SHORTAGE in e_flows_df.columns
    ):

        boolean = True

        test = [
            (
                e_flows_df[EXCESS_ELECTRICITY][t] != 0
                and e_flows_df[DEMAND_SHORTAGE][t] != 0
            )
            for t in e_flows_df.index
        ]

        if any(test) is False:
            boolean = False

        if boolean is False:
            logging.warning(
                "PLAUSABILITY TEST FAILED: Excess and shortage at the same time!"
            )
            oemof_results.update(
                {
                    COMMENTS: oemof_results[COMMENTS]
                    + "Excess and shortage at the same time. "
                }
            )

    return


def excess_feedin(oemof_results, e_flows_df):
    logging.debug("Plausibility test: Excess/Feedin")
    if (
        (EXCESS_ELECTRICITY in e_flows_df.columns)
        and (GRID_AVAILABILITY in e_flows_df.columns)
        and (FEED_INTO_MAIN_GRID in e_flows_df.columns)
    ):

        boolean = True

        test = [
            (
                (
                    (e_flows_df[EXCESS_ELECTRICITY][t] != 0)
                    and (
                        e_flows_df[FEED_INTO_MAIN_GRID][t]
                        != oemof_results[CAPACITY_PCC][t]
                    )
                )  # actual item!
                or (
                    (e_flows_df[EXCESS_ELECTRICITY][t] != 0)
                    and (e_flows_df[GRID_AVAILABILITY][t] == 0)
                )
            )
            for t in e_flows_df.index
        ]

        if any(test) is False:
            boolean = False

        if boolean is False:
            logging.warning(
                "PLAUSABILITY TEST FAILED: Excess while feedin to national grid not maximal (PCC capacity)!"
            )
            oemof_results.update(
                {COMMENTS: oemof_results[COMMENTS] + "Excess while feedin not maximal."}
            )

    return
