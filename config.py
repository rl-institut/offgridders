import pandas as pd

# Define solver
solver = 'cbc'
solver_verbose = False  # show/hide solver output

# Debugging
debug = True  # Set number_of_timesteps to 3 to get a readable lp-file.

# File paths
output_folder='./simulation_results'
output_file='micro_grid_simulation_results'

# Simulation timeframe
coding_process = False

if coding_process == True:
    time_start = pd.to_datetime('2018-07-07 0:00', format='%Y-%m-%d %H:%M')
    time_end = pd.to_datetime('2018-07-07 23:00', format='%Y-%m-%d %H:%M')
    time_frequency = 'H'
else:
    time_start = pd.to_datetime('2018-01-01 0:00', format='%Y-%m-%d %H:%M')
    time_end = pd.to_datetime('2018-12-31 23:00', format='%Y-%m-%d %H:%M')
    time_frequency = 'H'

#time_start = '1/1/2018'
#time_end = '31/12/2018'
#time_frequency = 'H'

#global date_time_index
date_time_index = pd.date_range(start=time_start, end=time_end, freq=time_frequency)

# Allow fuel shortage
allow_shortage = False
if allow_shortage == True:
    max_share_unsupplied_load = 0.05
    var_costs_unsupplied_load = 1

settings_fixed_capacities = False
setting_lp_file = False

# display_graphs
display_graphs_solar = False
display_graphs_demand = False
display_graphs_simulation = True
print_simulation_meta = True
print_simulation_main = True