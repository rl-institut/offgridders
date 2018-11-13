import pandas as pd


####### ----------------- General simulation settings ------------------- #######
coding_process              = True  # Defines timeframe and noise (see below)

# oemof simulation
allow_shortage              = False  # Allow supply shortage, details given below

# simulated cases:
simulated_cases = {
    'mg_fixed': True,
    'buyoff': False,
    'parallel': False,
    'adapted': False,
    'oem_interconnected': False,
    'backupgrid': False,
    'buysell': False,
    'mg_oem': False
}
# Minimal batch capacities (always round up, if value is exactly met, add another batch)
round_to_batch = {'PV': 0.25, # kWp
            'GenSet': 0.25, #kW
            'Storage': 1 #kWh
            }

# # # # # # # # #
# Input (files) #
# # # # # # # # #
use_input_file_demand       = True
use_input_file_weather      = False

if use_input_file_demand == True:
    input_file_demand       = './inputs/demand.csv'
    unit_of_input_file      = 'kWh'
    if unit_of_input_file == 'Wh': unit_factor = 1000
    elif unit_of_input_file == 'kWh': unit_factor = 1
    else: print ('WARNING! Unknown unit of demand file')

if use_input_file_weather == True:
    input_file_weather      = './inputs/weather.csv'

# # # # # #
# Outputs #
# # # # # #
write_demand_to_file = False
write_weather_to_file = False
if use_input_file_demand == True: write_demand_to_file = False
if use_input_file_weather == True: write_weather_to_file = False

# Output file paths
output_folder='./simulation_results'
output_file='results'

# display results and graphs
setting_lp_file             = False  # save lp file of oemof simulation
display_graphs_solar        = False
display_graphs_demand       = False
display_graphs_simulation   = False
print_simulation_meta       = False
print_simulation_main       = False

####### ----------------- Oemof simulation settings ------------------- #######
# Define solver
solver = 'cbc'
solver_verbose = False  # show/hide solver output

# Debugging
debug = True  # Set number_of_timesteps to 3 to get a readable lp-file.

####### ----------------- Input data for settings  ------------------- #######

# Simulation timeframe
if coding_process == True:
    evaluated_days          =  1 # not used to redifine time_start/end! manual!
    time_start              = pd.to_datetime('2018-07-07 0:00', format='%Y-%m-%d %H:%M')
    time_end                = pd.to_datetime('2018-07-07 23:00', format='%Y-%m-%d %H:%M')
    time_frequency          = 'H'
    white_noise_demand      = 0 # Percent
    white_noise_irradiation = 0 # Percent

else:
    time_start              = pd.to_datetime('2018-01-01 0:00', format='%Y-%m-%d %H:%M')
    time_end                = pd.to_datetime('2018-12-31 23:00', format='%Y-%m-%d %H:%M')
    time_frequency          = 'H'

    white_noise_demand      = 15 # Percent
    white_noise_irradiation = 15 # Percent

#global date_time_index
date_time_index = pd.date_range(start=time_start, end=time_end, freq=time_frequency)