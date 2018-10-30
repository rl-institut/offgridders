import pandas as pd

# Define solver
solver = 'cbc'
solver_verbose = False  # show/hide solver output

# Debugging
debug = False  # Set number_of_timesteps to 3 to get a readable lp-file.

# File paths
output_folder='./simulation_results'
output_file='micro_grid_simulation_results'

# define global variables
global display_graphs
display_graphs = False

# Simulation timeframe
# todo define time as one whole year aka 8760 timesteps - right now the 31st is not counted adequately
time_start = '1/1/2018'
time_end = '31/12/2018'
time_frequency = 'H'

global date_time_index
date_time_index = pd.date_range(start=time_start, end=time_end, freq=time_frequency)
