"""
Following excample: https://github.com/oemof/oemof_examples/blob/master/examples/oemof_0.2/basic_example/basic_example.py#L84

Energy system modeled: Micro Grid with fixed capacities

            input/output    bus_fuel        bus_electricity     flow
                    |               |               |
                    |               |               |
source: pv          |------------------------------>|       pv_generate (fix)
                    |               |               |
source: fossil_fuel |-------------->|               |       fossil_fuel_in (var)
                    |               |               |
trafo: generator    |<--------------|               |       fossil_fuel_use (var)
                    |------------------------------>|       generate (var)
                    |               |               |
sink: demand        |<------------------------------|       demand_supply (fix)
                    |               |               |
sink: excess        |<------------------------------|       excess_supply (var)
                    |               |               |
storage: battery    |<------------------------------|       store (var)
                    |------------------------------>|       feed_in_stored (var)
_____
Data used: None

_________
Requires: oemof, matplotlib

"""

###############################################################################
# Imports and initialize
###############################################################################

from oemof.tools import logger
from oemof.tools import helpers

import oemof.solph as solph
import oemof.outputlib as outputlib

import logging
import os
import pandas as pd
import matplotlib.pyplot as plt
import pprint as pp


# Define solver
solver = 'cbc'
solver_verbose = False  # show/hide solver output

# Debugging
debug = False  # Set number_of_timesteps to 3 to get a readable lp-file.

# Simulation timesteps
number_of_time_steps = 24*7*8

# Logging
logger.define_logging(logfile='energy_system_main.log',
                      screen_level=logging.INFO,
                      file_level=logging.DEBUG)

###############################################################################
# Initialize Energy System
###############################################################################

logging.info('Initialize the energy system')

# Create panda DataFrame
date_time_index = pd.date_range('1/1/2018', periods=number_of_time_steps, freq='H')

# create energy system
micro_grid_system = solph.EnergySystem(timeindex=date_time_index)

# Read data file
filename = os.path.join(os.path.dirname(__file__), 'data_rows_demand_pv_wind.csv')  # why do I need this function?
data_set = pd.read_csv(filename)

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

# create and add demand sink to micro_grid_system - fixed
micro_grid_system.add(solph.Sink(label="sink_demand",
                           inputs={bus_electricity_mg: solph.Flow(
                               actual_value=data_set['demand'],
                               nominal_value=1,
                               fixed=True)}  # utilizing imported data-set
                            ))

# create and add excess electricity sink to micro_grid_system - variable
micro_grid_system.add(solph.Sink(label="sink_excess",
                           inputs={bus_electricity_mg: solph.Flow()}
                                ))

# create and add fuel source to micro_grid_system - variable
micro_grid_system.add(solph.Source(label="source_fuel",
                             outputs={bus_fuel: solph.Flow(
                                 nominal_value=29825293,  #  ??
                                 summed_max=1)}  #  ??
                                   ))

# create and add pv generation source to micro_grid_system - fixed
micro_grid_system.add(solph.Source(label="source_pv",
                             outputs={bus_electricity_mg: solph.Flow(
                                 actual_value=data_set['pv'],  # utilizing imported data-set
                                 nominal_value=582000,   #  ??
                                 fixed=True)}  # do not resize imported values
                                   ))

# create and add fuel generator (transformer) to micro_grid_system - variable
micro_grid_system.add(solph.Transformer(label="transformer_fuel_generator",
                                  inputs={bus_fuel: solph.Flow()},
                                  outputs={bus_electricity_mg: solph.Flow(
                                      nominal_value=10e10,    #  ??
                                      variable_costs=50)},   #  necessary?
                                  conversion_factors={bus_electricity_mg: 0.58},  # is efficiency of the generator?? Then this should later on be included as a function of the load factor
                                        ))

# create and add storage object representing a battery - variable
storage = solph.components.GenericStorage(
    nominal_capacity=10077997,    #  ??
    label='storage',
    inputs={bus_electricity_mg: solph.Flow(nominal_value=10077997/6)},  # 10077997/6 is probably the maximum charge/discharge possible in one timestep
    outputs={bus_electricity_mg: solph.Flow(nominal_value=10077997/6, variable_costs=0.001)},
    capacity_loss=0.00,  # from timestep to timestep? what is this?
    initial_capacity=None,  # in terms of SOC?
    inflow_conversion_factor=1,  # storing efficiency?
    outflow_conversion_factor=0.8,  # efficiency of feed-in-stored?
)

micro_grid_system.add(storage)

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

# store energy system with results
micro_grid_system.dump(dpath='./Simulation_Results', filename='micro_grid_simulation_results')

# ****************************************************************************
# ********** PART 2 - Processing the results *********************************
# ****************************************************************************

logging.info('**** The script can be divided into two parts here.')
logging.info('Restore the energy system and the results.')
micro_grid_system = solph.EnergySystem()
micro_grid_system.restore(dpath='./Simulation_Results', filename='micro_grid_simulation_results')

# define an alias for shorter calls below (optional)
results = micro_grid_system.results['main']
storage = micro_grid_system.groups['storage']

# print a time slice of the state of charge
print('')
print('********* State of Charge (slice) *********')
print(results[(storage, None)]['sequences']['2018-02-25 08:00:00':
                                            '2018-02-26 15:00:00'])
print('')

# get all variables of a specific component/bus
custom_storage = outputlib.views.node(results, 'storage')
electricity_bus = outputlib.views.node(results, 'bus_electricity_mg')

# plot the time series (sequences) of a specific component/bus
if plt is not None:
    custom_storage['sequences'].plot(kind='line', drawstyle='steps-post')
    plt.show()
    electricity_bus['sequences'].plot(kind='line', drawstyle='steps-post')
    plt.show()

# print the solver results
print('********* Meta results *********')
pp.pprint(micro_grid_system.results['meta'])
print('')

# print the sums of the flows around the electricity bus
print('********* Main results *********')
print(electricity_bus['sequences'].sum(axis=0))