
import logging

class utilities:

class timeseries:
    def get_all:
        return

    # Check for saved blackout scenarios/grid availability, else continue randomization of backout events
    def get_shortage(case_dict):

        return

class plausability_tests:
    '''
    Checking oemof calculations for plausability. The most obvious errors should be identified this way.
    Ideally, not a single error should be displayed or added to the oemof comments.
    Checks include:
    - Demand <-> supplied demand <-> shortage
    - feedin <-> consumption
    - grid availability <-> feedin to grid
    - grid availability <-> consumption from grid
    - excess <-> shortage
    - excess <-> feedin > pcc cap
    - excess <-> grid availability
    '''

    def demand_supply_shortage (oemof_results, timeseries_demand, timeseries_demand_supply, timeseries_shortage):
        boolean = True
        if any(timeseries_demand_supply != timeseries_demand and timeseries_shortage == 0):
            boolean = False

        if boolean == False:
            logging.warning("ATTENTION: Demand not fully supplied but no shortage!")
            oemof_results.update({'comments': oemof_results['comments'] + 'Demand not fully supplied but no shortage. '})

        return


    def feedin_consumption(oemof_results, timeseries_grid_feedin, timeseries_grid_consumption):
        boolean = True

        if any(timeseries_grid_feedin != 0 and timeseries_grid_consumption != 0):
            boolean = False

        if boolean == False:
            logging.warning("ATTENTION: Feedin to and consumption from national grid at the same time!")
            oemof_results.update(
                {'comments': oemof_results['comments'] + 'Feedin to and consumption from national grid at the same time. '})

        return

    def gridavailability_feedin(oemof_results, timeseries_grid_feedin, timeseries_grid_availability):
        boolean = True

        if any(timeseries_grid_feedin != 0 and timeseries_grid_availability == 0):
            boolean = False

        if boolean == False:
            logging.warning("ATTENTION: Feedin to national grid during blackout!")
            oemof_results.update(
                {'comments': oemof_results['comments'] + 'Feedin to national grid during blackout. '})

        return

    def gridavailability_consumption(oemof_results, timeseries_grid_consumption, timeseries_grid_availability):
        boolean = True

        if any(timeseries_grid_consumption != 0 and timeseries_grid_availability == 0):
            boolean = False

        if boolean == False:
            logging.warning("ATTENTION: Consumption from national grid during blackout!")
            oemof_results.update(
                {'comments': oemof_results['comments'] + 'Consumption from national grid during blackout. '})

        return

    def excess_shortage(oemof_results, timeseries_excess, timeseries_shortage):
        boolean = True

        if any(timeseries_excess != 0 and timeseries_shortage != 0):
            boolean = False

        if boolean == False:
            logging.warning("ATTENTION: Excess and shortage at the same time!")
            oemof_results.update(
                {'comments': oemof_results['comments'] + 'Excess and shortage at the same time. '})

        return


    def excess_feedin(oemof_results, timeseries_excess, timeseries_grid_feedin, timeseries_grid_availability, pcc_cap):
        boolean = True

        if any(
                (timeseries_excess != 0 and timeseries_grid_feedin != pcc_cap)
                or (timeseries_excess != 0 and timeseries_grid_availability == 0)):
            boolean = False

        if boolean == False:
            logging.warning("ATTENTION: Feedin to national grid during blackout!")
            oemof_results.update(
                {'comments': oemof_results['comments'] + 'Feedin to national grid during blackout. '})

        return