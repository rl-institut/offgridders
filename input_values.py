import pandas as pd
from oemof.tools import economics

###############################################################################
# Input values
###############################################################################

# Define demand
# todo check for units of annual demand
ann_el_demand_per_household = 2210 # kWh/a
ann_el_demand_per_business = 10000 # kWh/a
number_of_households = 20
number_of_businesses = 6

demand_input = pd.DataFrame({'annual_demand_kWh': [ann_el_demand_per_household, ann_el_demand_per_business],
                             'number': [number_of_households, number_of_businesses]},
                            index=['households', 'businesses'])

# todo what exactly is wac
# todo include own loop for varying wacc values (calculating annuity based on wac, creating vector, add to sensitivity boundaries AND NOT to constant values
wacc = 0.05

# todo multiple commas, find out how to autpgeneratre min/max values if wacc is an interval, how to integrate min/max
# of costs if that is optional -> include in sensitivity bounds and use min=max?

cost_data = pd.DataFrame({'PV':         [20,            450,        0,          0],
                          'GenSet':     [15,            200,        0,          0],
                          'Storage':    [6,             170,        0,          0],
                          'PCoupling':  [20,            1500,       0,          0]},
                         index=         ['lifetime',    'capex',    'opex_a',   'opex_var'])

# Cost data
# todo annuity currently includes annual opex costs!!
cost_data.loc['annuity', 'PV']      =   economics.annuity(capex=cost_data.loc['capex', 'PV',], n=cost_data.loc['lifetime', 'PV'], wacc=wacc)\
                                        + cost_data.loc['opex_a', 'PV',]
cost_data.loc['annuity', 'GenSet']  =   economics.annuity(capex=cost_data.loc['capex', 'GenSet'], n=cost_data.loc['lifetime', 'GenSet'], wacc=wacc)\
                                        + cost_data.loc['opex_a', 'GenSet',]
cost_data.loc['annuity', 'Storage'] =   economics.annuity(capex=cost_data.loc['capex', 'Storage'], n=cost_data.loc['lifetime', 'Storage'], wacc=wacc)\
                                        + cost_data.loc['opex_a', 'Storage',]
cost_data.loc['annuity', 'PCoupling'] =   economics.annuity(capex=cost_data.loc['capex', 'PCoupling'], n=cost_data.loc['lifetime', 'PCoupling'], wacc=wacc)\
                                        + cost_data.loc['opex_a', 'PCoupling',]

from config import coding_process
if coding_process == True:
    from config import evaluated_days
    cost_data.loc['annuity']=cost_data.loc['annuity']/365*evaluated_days


# Define irradiation and generation
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

# todo check for units of irradiation and generation (sqm, panel)
pv_system_parameters=pd.DataFrame([surface_azimuth, tilt, module_name, inverter_name],
                       index=['surface_azimuth', 'tilt', 'module_name', 'inverter_name'],
                       columns=[pv_composite_name])

###############################################################################
# Sensitivity analysis
###############################################################################
# constants/values of the sensitivity analysis - influencing the base case OEM
'''
IT IS POSSIBLE TO SHIFT ELEMENTS BETWEEN THE LIST sensitivity_bounds <-> constant_values
BUT DO NOT DELETE OR ADD NEW ELEMENTS WITHOUT CHANGING THE MAIN CODE
'''
sensitivity_bounds ={
        #'price_fuel':     {'min': 0.5,  'max': 1,     'step': 0.1}
    }

# Values of the sensitivity analysis that appear constant
sensitivity_constants ={
        'cost_annuity_pv':              cost_data.loc['annuity', 'PV'], # incl o&M (scaled per kWp!!)
        'cost_annuity_genset':          cost_data.loc['annuity', 'GenSet'], # incl o&M (scaled per kWh!!)
        'cost_annuity_storage':         cost_data.loc['annuity', 'Storage'], # incl o&M (scaled per kW!!)
        'cost_annuity_pcoupling':       cost_data.loc['annuity', 'PCoupling'],  # todo PC not implemented
        'cost_var_pv':                  cost_data.loc['opex_var', 'PV'], # per unit # todo not implemented
        'cost_var_genset':              cost_data.loc['opex_var', 'GenSet'], # per unit # todo not implemented
        'cost_var_storage':             cost_data.loc['opex_var', 'PV'], # per unit # todo not implemented
        'cost_var_pcoupling':           cost_data.loc['opex_var', 'PCoupling'], # todo PC not implemented
        'price_fuel':                   1, # /unit
        'combustion_value_fuel':        9.41, # kWh/unit
        'price_electricity_main_grid':  0.20,  # todo not implemented
        'max_share_unsupplied_load':    0, #  factor
        'costs_var_unsupplied_load':    10, # /kWh
        'blackout_frequency':           7, #  blackouts per month
        'blackout_duration':            2, # hrs per blackout
        'storage_Crate':                1/6, # factor (possible charge/discharge ratio to total capacity)
        'storage_loss_timestep':        0, # factor
        'storage_inflow_efficiency':    0.8, # factor
        'storage_outflow_efficiency':   1,  # factor
        'storage_capacity_min':         0.2,  # factor 1-DOD
        'storage_capacity_max':         0.98,  # factor
        'storage_initial_soc':          None, # factor # todo: what does None mean here?
        'genset_efficiency':         0.58, #  factor
        'genset_min_loading':           0.2, # Minimal load factor of generator - TODO only effective in dispatch optimization, not OEM
        'genset_max_loading':           1,   # maximal load factor of generator
        'efficiency_pcoupling':         0.98, # inverter inefficiency between highvoltage/mediumvoltage grid (maybe even split into feedin/feedfrom
        'min_res_share':                0, # todo not implemented res share
        'distance_to_grid':             10 # todo not implemented distance_to_grid
    }