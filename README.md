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

# Energy system
_Based on file energysystem_main.py_
Currently a micro grid system with fixed demand, pv generation and a fossil fuelled generator. 

# PV generarion: 
_Based on file pv_generation.py_
As written in demandlib, the technical pv module parameters are taken from the sandia-files.
    
        https://sam.nrel.gov/sites/default/files/sam-library-sandia-modules-2015-6-30.csv
        https://sam.nrel.gov/sites/default/files/sam-library-cec-modules-2015-6-30.csv

# Load profile
_Based on file demand_profile_generation.py_