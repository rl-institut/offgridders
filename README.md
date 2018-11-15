# simulator_grid-connected_micro_grid
Simulates operational modes of a micro grid interconnecting to a weak national grid

Tasks:
- Simulate simple MG with fixed capacities

---- Specific PV generation

---- Plotting results

---- Specific load profile (demandlib?)

- Include economic package

- OEM of micro grid

https://guides.github.com/activities/hello-world/

# Needed packages
tables, pandas, tkinter

matplotlib

oemof, demandlib, pvlib

# Energy system
_Based on file energy_system_main.py_
Currently a micro grid system with fixed demand, pv generation and a fossil fuelled generator. 

# PV generarion: 
_Based on file pvlib_scripts.py_
General: As written in demandlib docs, technical pv module parameters are taken from the sandia-files.

        https://sam.nrel.gov/sites/default/files/sam-library-sandia-modules-2015-6-30.csv
        https://sam.nrel.gov/sites/default/files/sam-library-cec-modules-2015-6-30.csv
        
Solar irradiation (per sqm?) and pv generation (per panel?) are calculated based on location and a 
specific solar module and inverter from the sandia-files. They provide all technical parameters, only
tilt and azimuth are input parameters. Currently working with constant wind speed and ambient temperature.

The solar irradiation as well as the pv generation therefore are highly idealized, and can differ 
from the measured local values. The margin should be adressed somewhere in the thesis.

Currently, no white noise taking into account volatile weather conditions is included. 
The energy system currently receives the total irradiation as well as the panel generation for the
definition of its components. In the future, multiple panels should be integrated.

# Load profile
_Based on file demand_profile.py_
The demand profile estimation is based on the number and annual consumption of households and businesses 
at the project site. In the future, the interactive addition of further sectors could be interesting.

Currently, the script calculates the profile for each sector in 15-min, 1-hr and 1-d timesteps. 
Additionaly, the total consumption and the highest peak of a day are summarized. 
Plots for all cases are displayed, as well as other summarized values.
The energy system recieves the total consumption as the project demand profile.

# Track Versions

16.10: Installed Pycharm on personal and RLI PC

17.10: Github pull and push tested (working)

17.10: Created CSV file for cost input, py file for pandas reading

22.10: Sucessfully adapted oemof's basic_example (no wind), but plots are not created

23.10: Standalone completed: demandlib (demand profile) and multiple pv generation scripts
        (pv_generation_pv, pvlib_modelchain, pvlib_try)
        
24.10: Combined energy system with demand class (demand profile generation)

25.10: Combined energy system with pvlib class (solar irradiation, pv generation)

30.10: Integration of demand and pvlib class into Energysystem complete (fixed capacities)

31.10:  Definition of config/input file

1.11:  Integration of config/input file

2.11: Trying to fix OEM, using config/input file

5.11: Trying to fix OEM, creating basic modular structure

6.11: Fixed OEM in standalone script, started defining oemoffunctions for modular tool

7.11: Working oemfunctions, now easy definition and adoptation of multiple cases

12.11: Improved modular structure - now accepting files as demand input, base structure for sensitivity analyses included

13.11: Improved input file 

15.11: Issue with PV, storage (unsolved)