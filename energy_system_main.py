"""
Following excample:
https://github.com/oemof/oemof_examples/blob/master/examples/oemof_0.2/basic_example/basic_example.py#L84

Energy system modeled: Micro Grid with fixed capacities

            input/output    bus_fuel        bus_electricity     flow
                    |               |               |
                    |               |               |
source: pv          |------------------------------>|       generate_pv (fix)
                    |               |               |
source: fossil_fuel |-------------->|               |       fossil_fuel_in (var)
                    |               |               |
trafo: generator    |<--------------|               |       fossil_fuel_use (var)
                    |------------------------------>|       generate_fuel (var)
                    |               |               |
storage: battery    |<------------------------------|       battery_charge (var)
                    |------------------------------>|       battery_discharge (var)
                    |               |               |
sink: demand        |<------------------------------|       supply_demand (fix)
                    |               |               |
sink: excess        |<------------------------------|       supply_excess (var)
                    |               |               |

_____
Data used: None

_________
Requires: oemof, matplotlib

"""

###############################################################################
# Imports and initialize
###############################################################################

from oemof.tools import logger
# from oemof.tools import helpers

import oemof.solph as solph
import oemof.outputlib as outputlib

import logging
# Logging
logger.define_logging(logfile='energy_system_main.log',
                      screen_level=logging.INFO,
                      file_level=logging.DEBUG)

import os
import pandas as pd
import pprint as pp

# Try to import matplotlib librar
try:
    import matplotlib.pyplot as plt
except ImportError:
    logging.info('Attention! matplotlib could not be imported.')
    plt = None

# import own functions
from demand_profile import demand_profile
from pvlib_scripts import pvlib_scripts
###############################################################################
# Simulation settings
###############################################################################

# Define solver
solver = 'cbc'
solver_verbose = False  # show/hide solver output

# Debugging
debug = False  # Set number_of_timesteps to 3 to get a readable lp-file.

# Simulation timeframe
time_start = '1/1/2018'
time_end = '31/12/2018'
time_frequency = 'H'
date_time_index = pd.date_range(start=time_start, end=time_end, freq=time_frequency)

###############################################################################
# Input values
###############################################################################

# Definitions
fuel_price=0.04

# Define demand
ann_el_demand_per_household = 2210
ann_el_demand_per_business = 10000
number_of_households = 20
number_of_businesses = 6

demand_input = pd.DataFrame({'annual_demand_kWh': [ann_el_demand_per_household, ann_el_demand_per_business], 'number': [number_of_households, number_of_businesses]}, index=['households', 'businesses'])

# Define irradiation and generation
latitude = 50
longitude = 10
location_name = 'Berlin'
altitude = 34
timezone = 'Etc/GMT-1'

surface_azimuth = 180
tilt = 0
pv_composite_name = 'basic'
module_name = 'Canadian_Solar_CS5P_220M___2009_'
inverter_name = 'ABB__MICRO_0_25_I_OUTD_US_208_208V__CEC_2014_'

pv_system_location = pd.DataFrame([location_name, latitude, longitude, altitude, timezone],
                       index=['name', 'latitude', 'longitude', 'altitude', 'timezone'])

pv_system_parameters=pd.DataFrame([pv_composite_name, surface_azimuth, tilt, module_name, inverter_name],
                       index=['name','surface_azimut', 'tilt', 'module_name', 'inverter_name'])

solpos, dni_extra, airmass, pressure, am_abs, tl, cs = pvlib_scripts.irradiation(pv_system_location, date_time_index)

# File paths
output_folder='./simulation_results'
output_file='micro_grid_simulation_results'

input_folder='inputs'
input_file_demand_pv='data_rows_demand_pv_wind.csv'

# Read data file for demand, wind and pv

filename = os.path.join(os.path.dirname(__file__), input_folder+'/'+input_file_demand_pv)  # why do I need this function?
data_set = pd.read_csv(filename)


###############################################################################
# Initialize Energy System
###############################################################################

logging.info('Initialize the energy system')

# create energy system
micro_grid_system = solph.EnergySystem(timeindex=date_time_index)

# Estimate Load profile

demand_profile_Wh = demand_profile.estimate(demand_input) # wh? kWh?
###############################################################################
# Create Energy System with oemof
###############################################################################

logging.info('Create oemof objects for Micro Grid System (off-grid, fixed capacities)')

# create AC electricity bus of distribution grid
bus_electricity_mg = solph.Bus(label="bus_electricity_mg")

# create fuel bus
bus_fuel = solph.Bus(label="bus_fuel")

# add bus_electricity_mg and bus_fuel to micro_grid_system
micro_grid_system.add(bus_electricity_mg, bus_fuel)

# create and add fuel source to micro_grid_system - variable
source_fuel=solph.Source(label="source_fuel",
             outputs={bus_fuel: solph.Flow(
                 variable_costs=fuel_price)}  #  ??
            )

# create and add pv generation source to micro_grid_system - fixed
source_pv=solph.Source(label="source_pv",
             outputs={bus_electricity_mg: solph.Flow(
                 actual_value=data_set['pv'], # utilizing imported data-set
                 fixed=True,  #  ??
                 nominal_value=582000)}  # do not resize imported values
             )

# create and add demand sink to micro_grid_system - fixed
sink_demand=solph.Sink(label="sink_demand",
           inputs={bus_electricity_mg: solph.Flow(
               actual_value=demand_profile_Wh,
               nominal_value=1,
               fixed=True)}  # utilizing imported data-set
           )

# create and add excess electricity sink to micro_grid_system - variable
sink_excess=solph.Sink(label="sink_excess",
           inputs={bus_electricity_mg: solph.Flow()}
           )

# create and add fuel generator (transformer) to micro_grid_system - variable
transformer_fuel_generator=solph.Transformer(label="transformer_fuel_generator",
                  inputs={bus_fuel: solph.Flow()},
                  outputs={bus_electricity_mg: solph.Flow(
                      nominal_value=10e10,
                      variable_costs=50)},
                  conversion_factors={bus_electricity_mg: 0.58},  # is efficiency of the generator?? Then this should later on be included as a function of the load factor
                  )

# create and add storage object representing a battery - variable
generic_storage = solph.components.GenericStorage(
    nominal_capacity=10077997,  #  ??
    label='generic_storage',
    inputs={bus_electricity_mg: solph.Flow(nominal_value=10077997/6)},  # 10077997/6 is probably the maximum charge/discharge possible in one timestep
    outputs={bus_electricity_mg: solph.Flow(nominal_value=10077997/6, variable_costs=0.001)},
    capacity_loss=0.00,  # from timestep to timestep? what is this?
    initial_capacity=None,  # in terms of SOC?
    inflow_conversion_factor=1,  # storing efficiency?
    outflow_conversion_factor=0.8,  # efficiency of feed-in-stored?
)

micro_grid_system.add(sink_demand, sink_excess, source_fuel, source_pv, transformer_fuel_generator, generic_storage)

###############################################################################
# Optimise the energy system and plot the results
###############################################################################

logging.info('Optimise the energy system of the micro grid')

# initialise the operational model
model = solph.Model(micro_grid_system)

# if tee_switch is true solver messages will be displayed
logging.info('Solve the optimization problem')
model.solve(solver=solver, solve_kwargs={'tee': solver_verbose})

logging.info('Store the energy system with the results.')

# The processing module of the outputlib can be used to extract the results
# from the model transfer them into a homogeneous structured dictionary.

# add results to the energy system to make it possible to store them.
micro_grid_system.results['main'] = outputlib.processing.results(model)
micro_grid_system.results['meta'] = outputlib.processing.meta_results(model)

#todo Enter check for directory and create directory here!
# store energy system with results
micro_grid_system.dump(dpath=output_folder, filename=output_file)

# ****************************************************************************
# ********** PART 2 - Processing the results *********************************
# ****************************************************************************

logging.info('**** The script can be divided into two parts here.')
logging.info('Restore the energy system and the results.')
micro_grid_system = solph.EnergySystem()

micro_grid_system.restore(dpath=output_folder, filename=output_file)

# define an alias for shorter calls below (optional)
results = micro_grid_system.results['main']
storage = micro_grid_system.groups['generic_storage']

# print a time slice of the state of charge
print('')
print('********* State of Charge (slice) *********')
print(results[(storage, None)]['sequences']['2018-02-25 08:00:00':
                                            '2018-02-26 15:00:00'])
print('')

# get all variables of a specific component/bus
custom_storage = outputlib.views.node(results, 'generic_storage')
electricity_bus = outputlib.views.node(results, 'bus_electricity_mg')

# plot the time series (sequences) of a specific component/bus
#todo plots not working
if plt is not None:
    logging.info('Plotting: Generic storage')
    custom_storage['sequences'].plot(kind='line', drawstyle='steps-post')
    plt.show()
    logging.info('Plotting: Electricity bus')
    electricity_bus['sequences'].plot(kind='line', drawstyle='steps-post')
    plt.show()

# print the solver results
print('********* Meta results *********')
pp.pprint(micro_grid_system.results['meta'])
print('')

# print the sums of the flows around the electricity bus
print('********* Main results *********')
print(electricity_bus['sequences'].sum(axis=0))