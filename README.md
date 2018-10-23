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

Tracking:

16.10: Installed Pycharm on personal and RLI PC

17.10: Github pull and push tested (working)

17.10: Created CSV file for cost input, py file for pandas reading

22.10: Sucessfully adapted oemof's basic_example (no wind), but plots are not created

23.10: Standalone completed: demandlib (demand profile) and multiple pv generation scripts
        (pv_generation_pv, pvlib_modelchain, pvlib_try)

# Energy system
_Based on file energysystem_main.py_
Currently a micro grid system with fixed demand, pv generation and a fossil fuelled generator. 

# PV generarion: 
General: As written in demandlib docs, technical pv module parameters are taken from the sandia-files.

        https://sam.nrel.gov/sites/default/files/sam-library-sandia-modules-2015-6-30.csv
        https://sam.nrel.gov/sites/default/files/sam-library-cec-modules-2015-6-30.csv
        
_Based on file pv_generation.py_
- requires input data (temp,dhi,dni,vwind)
- not my favourite...
    
_Based on file pvlib_try.py_
As written in demandlib, the technical pv module parameters are taken from the sandia-files.
- detailed calculations, but only location, module/inverter parameters and temp_air/wind to be defined
- using sandia modules and inverters
- highly adaptable

_Based on file pvlib_modelchain.py_
As written in demandlib, the technical pv module parameters are taken from the sandia-files.
- ghi/dni/dhi/temp/wind should be defined
- using sandia modules and inverters
- can use different input sets - but most importantly works with very few inputs

# Load profile
_Based on file demand_profile_generation.py_
- Adjusted demandlib example
- Now calculates: 15-min, 1-hr, 1-d, total 1-d, peak -1d load profiles
- Generates plots and prints values