# simulator_grid-connected_micro_grid
Simulates operational modes of a micro grid interconnecting to a weak national grid. 
Currently a micro grid system with fixed demand, pv generation and a fossil fuelled 
generator. 

# Needed packages
* tables
* pandas
* tkinter
* matplotlib
* oemof
* demandlib
* pvlib

# Track Versions
05.12: MAJOR UPDATE! Updated output list, export of electricity_mg flows, added case interconnection_buy and oem_grid_tied_mg, 
       checked interconnection_buy/interconnection_buysell based on annuity/costs, 

04.12: MAJOR UPDATE! Updated output list, better generation of oemof results, case-specific evaliation of costs

03.12: Buysell case created (unfinished), links to grid_availability, delected class extract 

30.11: Started buysell case, deleted function "extract", included grid_availability

29.11: Blackouts, OEM with minimal loading

28.11: Blackouts 

27.11: Preparing Zambia working (master merge), more on white noise, result file, blackouts

26.11: Economics fixed (equal in OEM and fix), continue simulation with existing .oemof files, included white noise

23.11: Cost calculations include real annuities now, but still large margin between oem/fix AND between cost of 
       components according to calculations and according to OEM!! 
       eg. Objective value (annuity) of 246, when PV+Storage alone have annuity of 256!
 
22.11: Cost calculations currently are complete bull, as they are not related to the individual lifetimes.

21.11: Results include LCOE, NPV, fuel consumption (NPV has a pretty large margin, results in 1ct/kWh so improve on that), 
       enabled computation of nonconvex flow

20.11: Saving results in external file, including external pv output file (kWh/kWp), writing the WIKI

19.11: Storage and PV issue solved: Batch, storage=6(Flow1+Flow2)/2, multiple demand files, started including external weather file

15.11: Issue with PV, storage (unsolved)

13.11: Improved input file 

12.11: Improved modular structure - now accepting files as demand input, base structure for sensitivity analyses included

7.11: Working oemfunctions, now easy definition and adoptation of multiple cases

6.11: Fixed OEM in standalone script, started defining oemoffunctions for modular tool

5.11: Trying to fix OEM, creating basic modular structure

2.11: Trying to fix OEM, using config/input file

1.11:  Integration of config/input file

31.10:  Definition of config/input file

30.10: Integration of demand and pvlib class into Energysystem complete (fixed capacities)

25.10: Combined energy system with pvlib class (solar irradiation, pv generation)

24.10: Combined energy system with demand class (demand profile generation)

23.10: Standalone completed: demandlib (demand profile) and multiple pv generation scripts
        (pv_generation_pv, pvlib_modelchain, pvlib_try)

22.10: Sucessfully adapted oemof's basic_example (no wind), but plots are not created

17.10: Created CSV file for cost input, py file for pandas reading

17.10: Github pull and push tested (working)

16.10: Installed Pycharm on personal and RLI PC