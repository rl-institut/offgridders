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


# Define solver
solver  =   'cbc'
solver_verbose = False # show/hide solver output

#Debugging
debug = False # Set number_of_timesteps to 3 to get a readable lp-file.

# Simulation timesteps
number_of_time_steps = 24*7*8

# Logging
logger.define_logging(logfile='energy_system_main.log',
                      screen_level=logging.INFO,
                      file_level=logging.DEBUG)

###############################################################################
# Create Energy System
###############################################################################

logging.info('Initialize the energy system')

# Create panda DataFrame
date_time_index = pd.date_range('1/1/2018', periods=number_of_time_steps, freq='H')

# create energy system
micro_grid_system = solph.EnergySystem(timeindex=date_time_index)


# create AC electricity bus of distribution grid
bus_electricity_mg = Bus(label="bus_electricity_mg")

# create fuel bus
bus_fuel = Bus(label="bus_fuel")

# add bus_electricity_mg and bus_fuel to micro_grid_system
micro_grid_system.add(bus_electricity_mg, bus_fuel)

# create and add demand sink to micro_grid_system
micro_grid_system.add(Sink(label="sink_demand", inputs=(bus_electricity_mg: [])))

# create and add excess electricity sink to micro_grid_system
micro_grid_system.add(Sink(label="sink_excess", inputs=(bus_electricity_mg: [])))

# create and add source to micro_grid_system
micro_grid_system.add(Source(label="source_fuel", outputs=(bus_fuel: [])))

# create and add fuel generator (transformer) to micro_grid_system
micro_grid_system.add(Transformer(label="transformer_fuel_generator", inputs=(bus_fuel: []), outputs=(bus_electricity_mg: [])))

