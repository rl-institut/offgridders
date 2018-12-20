import pandas as pd

####### ------------ General simulation settings ----------------- #######
coding_process                  = False  # Defines timeframe and noise (see below)
restore_oemof_if_existant       = True  # If set to False, the directory with results is emptied!!
restore_blackouts_if_existant   = True
base_case_with_min_loading      = False   # If set to True, the generator capacity will be equal to peak demand in kW!

# TOdo allow multiple generators here (or even allow multiple generators in general??)

# simulated cases:
simulated_cases = {
    'offgrid_fixed': False,             # dispatch with base oem capacities
    'interconnected_buy': True,        # dispatch with interconnected main grid (only consumption)
    'interconnected_buysell': True,    # dispatch with interconnected main grid (consumption+feedin)
    'oem_grid_tied_mg': True,          # optimization of grid-tied mg (consumption+feedin)
    'sole_maingrid': True,             # supply only by main grid (allowed shortage variable)
    'buyoff': False, # todo not implemented
    'parallel': False, # todo not implemented
    'adapted': False, # todo not implemented
}

# oemof simulation
allow_shortage               = False  # Allow supply shortage, details given below
setting_batch_capacity       = True
include_stability_constraint = True

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
setting_save_lp_file                = False  # save lp file of oemof simulation
setting_save_oemofresults           = True   # save oemofresults to .oemof file
display_graphs_solar                = False
display_graphs_demand               = False
display_graphs_flows_storage        = True
display_graphs_flows_electricity_mg = True

print_simulation_meta       = False  # print information on opimization
print_simulation_main       = False  # print accumulated flows over electricity bus
print_simulation_invest     = False  # print investment results
print_simulation_experiment = False  # Print data on experiment run (sensitivity analysis)

# Choose flows saved to csv
setting_save_flows_storage          = True
setting_save_flows_electricity_mg   = True

# Choose results saves in csv
results_demand_characteristics      = True
results_blackout_characteristics    = True
results_annuities                   = True
results_costs                       = True

####### ----------------- Oemof simulation settings ------------------- #######
# Define solver
solver = 'cbc'
solver_verbose       = False  # show/hide solver output
cmdline_option       = 'ratioGap' #  options for solver: allowedGap,  mipgap, ratioGap
cmdline_option_value = 1*10**(-1)

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