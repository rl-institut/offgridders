# -*- coding: utf-8 -*-
"""
STANDALONE VERSION
Unchanged file:
https://github.com/oemof/demandlib/blob/master/demandlib/examples/power_demand_example.py
Demandlib documentation:
https://demandlib.readthedocs.io/en/latest/
https://learn.adafruit.com/micropython-basics-loading-modules/import-code
"""

import datetime
import demandlib.bdew as bdew
import demandlib.particular_profiles as profiles
from datetime import time as settime
try:
    import matplotlib.pyplot as plt
except ImportError:
    print("Matplotlib.pyplot could not be loaded")
    plt = None

class estimate:

    # todo difference between class and function
    # todo better display of plots
    def plot_results(pandas_dataframe, title, xaxis, yaxis):
        if plt is not None:
            # Plot demand
            ax = pandas_dataframe.plot()
            ax.set_title(title)
            ax.set_xlabel(xaxis)
            ax.set_ylabel(yaxis)
            plt.show()
        return

    def power_example(demand_input):
        year = 2018

        # todo: in gui, it must be possible to add holidays and scaling parameters manually
        # todo: in gui, it must be possible to set and scale for working hours
        holidays = {
            datetime.date(2018, 1, 1): 'New year',
            datetime.date(2018, 12, 25): 'Christmas Day',
            datetime.date(2018, 12, 26): 'Second Christmas Day'
        }
        # todo: create seasons
        """ 
        seasons (dictionary) – Describing the time ranges for summer, winter and transition periods.
        seasons = {}
        """

        ann_el_demand_per_sector = demand_input.annual_demand_kWh*demand_input.number # todo is this a value that should be submitted as kWh/a or Wh/a

        #{
        #    'households': ann_el_demand_per_household*number_of_households,
        #    'businesses': ann_el_demand_per_business*number_of_businesses
        #}

        # read standard load profiles
        e_slp = bdew.ElecSlp(year, holidays=holidays)

        # multiply given annual demand with timeseries
        electricity_demand = e_slp.get_profile(ann_el_demand_per_sector)

        # todo: industial group might not be be used properly with households/businesses
        # todo: if more sectors are to be included, what has to change with the code?
        # Add the slp for the industrial group
        ilp = profiles.IndustrialLoadProfile(e_slp.date_time_index,
                                             holidays=holidays)

        # Household profile: Factors by default
        # -> weekends have higher demand than weekdays
        electricity_demand['households'] = ilp.simple_profile(
            ann_el_demand_per_sector['households'])

        # Business profile: Beginning and end of workday, weekdays and weekend days, and scaling
        # -> weekends have lower demand that weekdays
        electricity_demand['businesses'] = ilp.simple_profile(
            ann_el_demand_per_sector['businesses'],
            am=settime(9, 0, 0), # Set beginning of workday to 9 am
            pm=settime(19,0,0), # Set end of workday to 19
            profile_factors={'week': {'day': 1.0, 'night': 0.8},
                             'weekend': {'day': 0.8, 'night': 0.6}})

        # todo if pass frequency/timestamp, then we automatically have appropriate demand profile. choose with check for frequency, which outputs (prints, plots) are generated
        # Define electricity demand profile with 15-min steps
        electricity_demand_15min = electricity_demand
        estimate.plot_results(electricity_demand, "Electricity demand per sector (15-min)", "Date (15-min steps)", "Date (15-min steps)")

        # Define total electricity demand profile with 15-min steps
        electricity_demand__total_15min = electricity_demand_15min['households']+electricity_demand_15min['businesses']
        print("Total annual demand for project site (kWh/a)")
        print(electricity_demand__total_15min.sum()/4)
        print(" ")
        estimate.plot_results(electricity_demand__total_15min, "Electricity demand at project site (15-min)", "Date (15-im steps)",
                     "Power demand in kW")

        """
        Be aware that the values in the DataFrame are 15minute values with
        a power unit. If you sum up a table with 15min values the result
        will be of the unit 'kW15minutes'. 
        You can divide the total sum electricity_demand.sum() by 4 to get kWh.
        For an hourly profile resample the DataFrame to hourly values using 
        the mean() method.
        """
        # Resample 15-minute values to hourly values.
        electricity_demand_hourly = electricity_demand.resample('H').mean()
        print("Total annual demand per sector (kWh/a)")
        print(electricity_demand_hourly.sum())
        print(" ")
        estimate.plot_results(electricity_demand_hourly, "Electricity demand per sector (1-hr)", "Date (1-hr steps)",
                     "Power demand in kW")

        # Total demand (hourly) for project site
        electricity_demand_total_hourly = electricity_demand_hourly['households']+electricity_demand_hourly['businesses']
        print("Total annual demand for project site (kWh/a)")
        print(electricity_demand_total_hourly.sum())
        print(" ")
        estimate.plot_results(electricity_demand_total_hourly, "Electricity demand at project site (1-hr)", "Date (1-hr steps)",
                     "Power demand in kW")

        # Resample hourly values to daily values.
        electricity_demand_daily = electricity_demand_hourly.resample('D').sum()
        estimate.plot_results(electricity_demand_daily, "Electricity demand per sector (1-d)", "Date (1-d steps)",
                     "Power demand in kWh/d")
        print("Median daily demand (kWh/d)")
        print(electricity_demand_daily.mean())
        print(" ")

    # todo include white noise

        # Define daily profile with peak demands - without white noise the value is constant
        electricity_demand_kW_max = electricity_demand.resample('D').max()
        estimate.plot_results(electricity_demand_kW_max, "Daily peak demand per sector", "Date (1-d steps)",
                     "Peak power demand in kW")
        print("Absolute peak demand (kW)")
        print(electricity_demand_kW_max.max())
        print(" ")

        print(electricity_demand_total_hourly)

        return electricity_demand_total_hourly
    # todo create merged demand of households and businesses, so that the total load profile can be fed into the mg optimization

if __name__ == '__main__':
    power_example()