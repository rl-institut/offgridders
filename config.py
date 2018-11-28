import pandas as pd

####### ------------ General simulation settings ----------------- #######
coding_process              = True  # Defines timeframe and noise (see below)
restore_oemof_if_existant   = False   # If set to False, the directory with results is emptied!!

# simulated cases:
simulated_cases = {
    'mg_fixed': True, # dispatch with base oem capacities
    'buyoff': False,
    'parallel': False,
    'adapted': False,
    'oem_interconnected': False,
    'backupgrid': False,
    'buysell': False
}

# oemof simulation
allow_shortage              = False  # Allow supply shortage, details given below
setting_batch_capacity      = True

####### ----------------- Settings for files------------------- #######
# Input (files)
use_input_file_demand       = True
use_input_file_weather      = True
# Outputs
write_demand_to_file = False
write_weather_to_file = False
if use_input_file_demand == True: write_demand_to_file = False
if use_input_file_weather == True: write_weather_to_file = False

# Output file paths
output_folder='./simulation_results'
output_file='results'

# display results and graphs
setting_save_lp_file        = False  # save lp file of oemof simulation
setting_save_oemofresults   = True   # save oemofresults to .oemof file
display_graphs_solar        = False
display_graphs_demand       = False
display_graphs_simulation   = False
print_simulation_meta       = False  # print information on opimization
print_simulation_main       = False  # print accumulated flows over electricity bus
print_simulation_invest     = False  # print investment results
print_simulation_experiment = False  # Print data on experiment run (sensitivity analysis)

####### ----------------- Oemof simulation settings ------------------- #######
# Define solver
solver = 'cbc'
solver_verbose       = False  # show/hide solver output
cmdline_option       = 'ratioGap' #  options for solver: allowedGap,  mipgap, ratioGap
cmdline_option_value = 1*10**(-6)

# Debugging
debug = True  # Set number_of_timesteps to 3 to get a readable lp-file.

####### ----------------- Input data for settings  ------------------- #######

# Simulation timeframe
if coding_process == True:
    evaluated_days  =  1
    time_start      = pd.to_datetime('2018-07-07 0:00', format='%Y-%m-%d %H:%M')
    time_end        = time_start + pd.DateOffset(days=evaluated_days) - pd.DateOffset(hours=1)
    time_frequency  = 'H'

else:
    evaluated_days = 365
    time_start     = pd.to_datetime('2018-01-01 0:00', format='%Y-%m-%d %H:%M')
    time_end       = time_start + pd.DateOffset(days=evaluated_days) - pd.DateOffset(hours=1)
    time_frequency = 'H'
    # date_time_index.freq checkts for frequency, but result is sth like <Hour> or <15 * Minutes>


date_time_index = pd.date_range(start=time_start, end=time_end, freq=time_frequency)