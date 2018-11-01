import pandas as pd
from oemof.tools import economics

###############################################################################
# Input values
###############################################################################

# Definitions
fuel_price=0.04 # Euro/l

# Define demand
# todo check for units of annual demand
ann_el_demand_per_household = 2210 # kWh/a
ann_el_demand_per_business = 10000 # kWh/a
number_of_households = 20
number_of_businesses = 6

# Fixed capacities
# todo check for units of capacities
cap_pv          = 100 # in number of panels -> installed kWp depends on panel type chosen!
cap_fuel_gen    = 100 # kW
cap_storage     = 100 # kWh, max. charge/discharge per timestep: cap_pv/6 kWh

# todo what exactly is wac
# todo capex should include replacement costs etc... where account for annual costs?
wacc = 0.05
cost_data = pd.DataFrame({'PV': [400, 20, 100],
                          'GenSet': [300, 20, 2000],
                          'Storage': [170, 20, 100]},
                         index=['initial_investment', 'lifetime', 'capex'])

# Define irradiation and generation
location_name = 'Berlin'
latitude = 50
longitude = 10
altitude = 34
timezone = 'Etc/GMT-1'

pv_composite_name = 'basic'
surface_azimuth = 180
tilt = 0
module_name = 'Canadian_Solar_CS5P_220M___2009_'
inverter_name = 'ABB__MICRO_0_25_I_OUTD_US_208_208V__CEC_2014_'

###############################################################################
# Preprocessing
###############################################################################

demand_input = pd.DataFrame({'annual_demand_kWh': [ann_el_demand_per_household, ann_el_demand_per_business],
                             'number': [number_of_households, number_of_businesses]},
                            index=['households', 'businesses'])
# Cost data
cost_data.loc['annuity', 'PV']      =   economics.annuity(capex=cost_data.loc['capex', 'PV',], n=cost_data.loc['lifetime', 'PV'], wacc=wacc)
cost_data.loc['annuity', 'GenSet']  =   economics.annuity(capex=cost_data.loc['capex', 'GenSet'], n=cost_data.loc['lifetime', 'GenSet'], wacc=wacc)
cost_data.loc['annuity', 'Storage'] =   economics.annuity(capex=cost_data.loc['capex', 'Storage'], n=cost_data.loc['lifetime', 'Storage'], wacc=wacc)

pv_system_location = pd.DataFrame([latitude, longitude, altitude, timezone],
                       index=['latitude', 'longitude', 'altitude', 'timezone'],
                        columns=[location_name])

# todo check for units of irradiation and generation (sqm, panel)
pv_system_parameters=pd.DataFrame([surface_azimuth, tilt, module_name, inverter_name],
                       index=['surface_azimuth', 'tilt', 'module_name', 'inverter_name'],
                       columns=[pv_composite_name])