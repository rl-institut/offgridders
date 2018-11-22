import pandas as pd
from oemof.tools import economics

###############################################################################
# Optional values
###############################################################################
from config import use_input_file_demand, use_input_file_weather, setting_batch_capacity, coding_process
#----------------------------Demand profile-----------------------------------#
#TODO: ALLOW MULTIPLE DEMAND FILES
if use_input_file_demand == True:
    input_files_demand       = {#'demand_low':        './inputs/demand_zambia_low.csv',
                                #'demand_high':       './inputs/demand_zambia_high.csv',
                                'demand_median':     './inputs/demand_zambia_median.csv'
                                }
    unit_of_input_file      = 'kWh'
    if unit_of_input_file == 'Wh': unit_factor = 1000
    elif unit_of_input_file == 'kWh': unit_factor = 1
    else: print ('WARNING! Unknown unit of demand file')
else:
    # todo check for units of annual demand
    ann_el_demand_per_household = 2210  # kWh/a
    ann_el_demand_per_business = 10000  # kWh/a
    number_of_households = 20
    number_of_businesses = 6
    demand_input = pd.DataFrame({'annual_demand_kWh': [ann_el_demand_per_household, ann_el_demand_per_business],
                                 'number': [number_of_households, number_of_businesses]},
                                index=['households', 'businesses'])

#----------------------------Weather data------------------------------------#
if use_input_file_weather == True:
    input_file_weather      = './inputs/pv_gen_zambia.csv'
else:
    location_name = 'Berlin'
    latitude = 50
    longitude = 10
    altitude = 34
    timezone = 'Etc/GMT-1'

    pv_system_location = pd.DataFrame([latitude, longitude, altitude, timezone],
                                      index=['latitude', 'longitude', 'altitude', 'timezone'],
                                      columns=[location_name])

    pv_composite_name = 'basic'
    surface_azimuth = 180
    tilt = 0
    module_name = 'Canadian_Solar_CS5P_220M___2009_'
    inverter_name = 'ABB__MICRO_0_25_I_OUTD_US_208_208V__CEC_2014_'

    pv_system_parameters = pd.DataFrame([surface_azimuth, tilt, module_name, inverter_name],
                                        index=['surface_azimuth', 'tilt', 'module_name', 'inverter_name'],
                                        columns=[pv_composite_name])

#----------------------------Batch capacities---------------------------------#
if setting_batch_capacity == True:
    # Minimal batch capacities (always round up, if value is exactly met, add another batch)
    round_to_batch = {
        'PV': 0.25, # kWp
        'GenSet': 0.25, #kW
        'Storage': 1 #kWh
            }

#----------------------------White noise---------------------------------#
# todo not implemented
if coding_process == True:
    white_noise_demand      = 0
    white_noise_irradiation = 0
else:
    white_noise_demand      = 0.15
    white_noise_irradiation = 0.15

###############################################################################
# General Inputs and sensitivity analysis
###############################################################################
# constants/values of the sensitivity analysis - influencing the base case OEM
'''
IT IS POSSIBLE TO SHIFT ELEMENTS BETWEEN THE LIST sensitivity_bounds <-> constant_values
BUT DO NOT DELETE OR ADD NEW ELEMENTS WITHOUT CHANGING THE MAIN CODE
'''

sensitivity_bounds = {
    #'price_fuel':     {'min': 0.5,  'max': 1,     'step': 0.1}
    }

# Values of the sensitivity analysis that appear constant
sensitivity_constants = {
    'blackout_duration':	            2,	#	hrs	per	blackout
    'blackout_frequency':	            7,	#	blackouts	per	month
    'combustion_value_fuel':	        10,	#	kWh/unit
    'costs_var_unsupplied_load':	    10,	#	/kWh
    'distance_to_grid':	                10,	#	todo	not	implemented	distance_to_grid
    'genset_cost_investment':	        800,
    'genset_cost_opex':	                25,
    'genset_cost_var':	                0.023,
    'genset_efficiency':	            0.33,	#	factor
    'genset_lifetime':	                10,
    'genset_max_loading':	            1,	#	maximal	load	factor	of	generator
    'genset_min_loading':	            0,	#	Minimal	load	factor	of	generator	-	TODO	only	effective	in	dispatch	optimization,	not	OEM
    'max_share_unsupplied_load':	    0,	#	factor
    'min_res_share':	                0,	#	todo	only	works	properly	for	off-grid	oem!	Create	add.	transformer	with	input	streams	fuel	(0%	res)	+	nat.grid	(x%	res)	and	limit	resshare	there!	#does	not	work	at	all	for	dispatch	oem
    'pcoupling_cost_investment':	    1500,
    'pcoupling_cost_opex':	            0,
    'pcoupling_cost_var':	            0,
    'pcoupling_efficiency':	            0.98,	#	inverter	inefficiency	between	highvoltage/mediumvoltage	grid	(maybe	even	split	into	feedin/feedfrom
    'pcoupling_lifetime':	            20,
    'price_electricity_main_grid':	    0.20,	#	/unit
    'price_fuel':	                    4.4,	#	/unit
    'project_cost_fix':	                0,	#	not	implemented
    'project_cost_opex':	            0,	#	not	implemented
    'project_life':	                    20,
    'pv_cost_investment':	            950,
    'pv_cost_opex':	                    0,
    'pv_cost_var':	                    0,
    'pv_lifetime':	                    20,
    'storage_capacity_max':	            1,	#	factor
    'storage_capacity_min':	            0.2,	#	factor	1-DOD
    'storage_cost_investment':	        800,
    'storage_cost_opex':	            0,
    'storage_cost_var':	                0,
    'storage_Crate':	                1,	#	factor	(possible	charge/discharge	ratio	to	total	capacity)
    'storage_inflow_efficiency':	    0.9,	#	factor
    'storage_initial_soc':	            None,	#	factor	#	todo:	what	does	None	mean	here?
    'storage_lifetime':	                6,
    'storage_loss_timestep':	        0,	#	factor
    'storage_outflow_efficiency':	    0.9,	#	factor
    'tax':	                            0,
    'wacc':	                            0.12
}