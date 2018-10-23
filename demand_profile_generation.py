# -*- coding: utf-8 -*-
"""
STANDALONE VERSION
Unchanged file
https://github.com/oemof/demandlib/blob/master/demandlib/examples/power_demand_example.py
"""

import datetime
import demandlib.bdew as bdew
import demandlib.particular_profiles as profiles
from datetime import time as settime
try:
    import matplotlib.pyplot as plt
except ImportError:
    print("yeah, we see this")
    plt = None

# todo: in gui, it must be possible to add holidays and scaling parameters manually
# todo: in gui, it must be possible to set and scale for working hours
holidays = {
    datetime.date(2018, 1, 1): 'New year',
    datetime.date(2018, 12, 25): 'Christmas Day',
    datetime.date(2018, 12, 26): 'Second Christmas Day'
}

# Define demand
ann_el_demand_per_household = 2210
ann_el_demand_per_business = 10000
number_of_households = 20
number_of_businesses = 6

def power_example():
    year = 2018

    ann_el_demand_per_sector = {
        'households': ann_el_demand_per_household*number_of_households,
        'businesses': ann_el_demand_per_business*number_of_businesses
    }

    # read standard load profiles
    e_slp = bdew.ElecSlp(year, holidays=holidays)

    # multiply given annual demand with timeseries
    electricity_demand = e_slp.get_profile(ann_el_demand_per_sector)

    # todo: industial group might not be be used properly with households/businesses
    # Add the slp for the industrial group
    ilp = profiles.IndustrialLoadProfile(e_slp.date_time_index,
                                         holidays=holidays)

    # Beginning and end of workday, weekdays and weekend days, and scaling
    # factors by default
    electricity_demand['households'] = ilp.simple_profile(ann_el_demand_per_sector['households'])

    # Change scaling factors
    electricity_demand['businesses'] = ilp.simple_profile(
        ann_el_demand_per_sector['businesses'],
        am=settime(9, 0, 0), # Set beginning of workday to 9 am
        profile_factors={'week': {'day': 1.0, 'night': 0.8},
                         'weekend': {'day': 0.8, 'night': 0.6}})

    print("Be aware that the values in the DataFrame are 15minute values with "
          "a power unit. If you sum up a table with 15min values the result "
          "will be of the unit 'kW15minutes'.")

    print(electricity_demand.sum())

    print("You will have to divide the result by 4 to get kWh.")
    print(electricity_demand.sum() / 4)

    print("Or resample the DataFrame to hourly values using the mean() "
          "method.")

    # Resample 15-minute values to hourly values.
    electricity_demand = electricity_demand.resample('H').mean()
    print(electricity_demand.sum())

    if plt is not None:
        # Plot demand
        ax = electricity_demand.plot()
        ax.set_xlabel("Date")
        ax.set_ylabel("Power demand")
        plt.show()

if __name__ == '__main__':
    power_example()