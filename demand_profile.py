# -*- coding: utf-8 -*-
"""
Integrated version
Unchanged file:
https://github.com/oemof/demandlib/blob/master/demandlib/examples/power_demand_example.py
Demandlib documentation:
https://demandlib.readthedocs.io/en/latest/
https://learn.adafruit.com/micropython-basics-loading-modules/import-code
"""

import datetime
import pandas as pd
import demandlib.bdew as bdew
import demandlib.particular_profiles as profiles
from datetime import time as settime

import oemof.outputlib as outputlib
import logging

try:
    import matplotlib.pyplot as plt
except ImportError:
    print("Matplotlib.pyplot could not be loaded")
    plt = None

# Import simulation settings
from config import display_graphs_demand, date_time_index

class demand:
    # todo better display of plots
    def plot_results(pandas_dataframe, title, xaxis, yaxis, demand_title):
        from config import output_folder
        if plt is not None:
            if display_graphs_demand==True:
                # Plot demand
                ax = pandas_dataframe.plot()
                ax.set_title(title)
                ax.set_xlabel(xaxis)
                ax.set_ylabel(yaxis)
                plt.show()
                #plt.savefig(output_folder+'/fig_'+demand_title+'.png', bbox_inches='tight')
        return

    ##
    def get():
        from config import use_input_file_demand, write_demand_to_file

        if use_input_file_demand == True:
            demand_profile = demand.read_from_file() # results in a dictionary of demand profiles
        else:
            demand_profile = demand.demandlib_estimation()
            if write_demand_to_file == True:
                from config import output_folder
                demand_profile.to_csv(output_folder + '/demand.csv') # Save annual profile to file
            demand_profile = {'demand': demand_profile[date_time_index]} # utilize only defined timeframe for simulation

        return demand_profile

    def read_from_file():
        from input_values import input_files_demand, unit_factor
        from config import date_time_index

        demand_profiles =  {}
        for file in input_files_demand:
            data_set = pd.read_csv(input_files_demand[file])
            # Anpassen des timestamps auf die analysierte Periode
            index = pd.DatetimeIndex(data_set['timestep'].values)
            index = [item + pd.DateOffset(year=date_time_index[0].year) for item in index]
            # Reading demand profile adjusting to kWh
            demand_profile =  pd.Series(data_set['demand'].values/unit_factor, index = index)
            # todo Actually, there needs to be a check for timesteps 1/0.25 here
            logging.info('Included demand profile input file "'+ input_files_demand[file] + '"')
            logging.info('     Total annual demand at project site (kWh/a): ' + str(round(demand_profile.sum())))
            demand.plot_results(demand_profile[date_time_index], "Electricity demand at project site (" + file + ")",
                            "Date",
                            "Power demand in kW", file)
            demand_profiles.update({file: demand_profile[date_time_index]})
        return demand_profiles

    def demandlib_estimation():
        from input_values import demand_input
        from config import date_time_index
        year = date_time_index[0].year
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
        demand.plot_results(electricity_demand, "Electricity demand per sector (15-min)", "Date (15-min steps)", "Date (15-min steps)")

        # Define total electricity demand profile with 15-min steps
        electricity_demand__total_15min = electricity_demand_15min['households']+electricity_demand_15min['businesses']
        logging.info("Total annual demand for project site (kWh/a): " + str(round(electricity_demand__total_15min.sum()/4, 2)))
        demand.plot_results(electricity_demand__total_15min, "Electricity demand at project site (15-min)", "Date (15-im steps)",
                     "Power demand in kW", "demand_15min")

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
        logging.info("Total annual demand per sector (kWh/a): " + str(round(electricity_demand_hourly.sum())))
        demand.plot_results(electricity_demand_hourly, "Electricity demand per sector (1-hr)", "Date (1-hr steps)",
                     "Power demand in kW", "demand_sector_1hr")

        # Total demand (hourly) for project site
        electricity_demand_total_hourly = electricity_demand_hourly['households']+electricity_demand_hourly['businesses']
        logging.info("Total annual demand for project site (kWh/a): " + str( round(electricity_demand_total_hourly.sum()), 2))
        demand.plot_results(electricity_demand_total_hourly, "Electricity demand at project site (1-hr)", "Date (1-hr steps)",
                     "Power demand in kW", "demand_1hr")

        # Resample hourly values to daily values.
        electricity_demand_daily = electricity_demand_hourly.resample('D').sum()
        demand.plot_results(electricity_demand_daily, "Electricity demand per sector (1-d)", "Date (1-d steps)",
                     "Power demand in kWh/d", "demand_sector_1d")
        logging.info("Median daily demand per consumer (kWh/d): " + str( round(electricity_demand_daily.mean()/demand_input.number), 3))

    # todo include white noise

        # Define daily profile with peak demands - without white noise the value is constant
        electricity_demand_kW_max = electricity_demand.resample('D').max()
        demand.plot_results(electricity_demand_kW_max, "Daily peak demand per sector", "Date (1-d steps)",
                     "Peak power demand in kW", "demand__peak_sector_1d")
        logging.info("Absolute peak demand per sector (kW): " + str( round(electricity_demand_kW_max.max(),2)))
        return electricity_demand_total_hourly # to synchronize evaluated timeframe
    # todo create merged demand of households and businesses, so that the total load profile can be fed into the mg optimization