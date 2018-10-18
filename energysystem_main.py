from oemof.network import *
from oemof.energy_system import *

# create energy system
micro_grid_system = EnergySystem()


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

