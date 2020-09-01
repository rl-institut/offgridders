==========================================
Component library: oemof_generatemodel.py
==========================================

For a deep insight into Offgridders energy system model, the components are presented below. This information is mainly important for developers that are thinking of changing module `G` (especially `G0` and `G2a`), eg. when adding new assets.

To ease the definition of the models cases, a library of the utilized buses and components for the oemof model was generated. By combining them, the cases analyze specific energy systems with equal input parameters. The connections to the energy system model of oemof are automatically created, when a function is called.

Buses
------------------------------------------

* **bus_basic** (*micro_grid_system*):
    Creates basic fuel bus "bus_fuel" for the generator and the micro grids electricity bus "bus_electricity_mg".

* **bus_el_ng** (*micro_grid_system*):
    Creates electricity bus of national grid "bus_electricity_ng".

Sources
------------------------------------------

* **fuel_oem** (*micro_grid_system*, *bus_fuel*, *experiment*, *total_demand*):
    Creates fuel source "source_fuel" for OEM, including variable costs (based on fuel price and combustion value) and renewable share. ATTENTION: May this lead to infeasible OEM, if generator has minimal load share???

* **fuel_fix** (*micro_grid_system*, *bus_fuel*, *experiment*):
    Creates fuel source "source_fuel" for fix capacity scenarios, ALWAYS without boundary condition of renewable share, as this can create infeasible scenarios.

* **shortage** (*micro_grid_system*, *bus_electricity_mg*, *sum_demand_profile*, *experiment*):
    Creates source for shortages "source_shortage" including boundary conditions  for maximal unserved demand and the variable costs of unserved demand.

* **maingrid** (*micro_grid_system*, *bus_electricity_ng*, *price_electricity_main_grid*, *experiment*):
    Creates main grid electricity source "source_maingrid" with variable_costs (electricity price).

Components
------------------------------------------

* **pv_fix** (*micro_grid_system*, *bus_electricity_mg*, *pv_generation_per_kWp*, *capacity_pv*, *experiment*):
    Creates PV generation source "source_pv" with fix capacity, using the PV generation profile per kWp (scaled by capacity) with variable costs.

* **pv_oem** (*micro_grid_system*, *bus_electricity_mg*, *pv_generation_per_kWp*, *experiment*):
    Creates PV generation source "source_pv" for OEM, using the normed PV generation profile per kWp, investment costs and variable costs.

* **genset_fix** (*micro_grid_system*, *bus_fuel*, *bus_electricity_mg*, *capacity_fuel_gen*, *experiment*):
    Generates fossil-fueled genset "transformer_fuel_generator" with nonconvex flow (min and max loading), generator efficiency, fixed capacity and variable costs. If minimal loading = 0, the generator is modeled without a nonconvex flow (which would result in an error due to constraint 'NonConvexFlow.min').

* **genset_oem** (*micro_grid_system, bus_fuel, bus_electricity_mg, experiment*):
    Generates fossil-fueled genset "transformer_fuel_generator" for OEM with generator efficiency, investment and variable costs.

* **pointofcoupling_feedin_fix** (*micro_grid_system, bus_electricity_mg, bus_electricity_ng, capacity_pointofcoupling, experiment*):
    Creates point of coupling "pointofcoupling_feedin" with fixed capacity, conversion factor and variable costs for the feed into the national grid.

* **pointofcoupling_feedin_oem** (*micro_grid_system, bus_electricity_mg, bus_electricity_ng, experiment*):
    Creates point of coupling "pointofcoupling_feedin" for OEM, conversion factor, investment and variable costs for the feed into the national grid.

* **pointofcoupling_tomg_fix** (*micro_grid_system, bus_electricity_mg, bus_electricity_ng, cap_pointofcoupling, experiment*):
    Creates point of coupling "pointofcoupling_feedin" with fixed capacity, conversion factor and variable costs for the consumption from the national grid.

* **pointofcoupling_tomg_oem** (*micro_grid_system, bus_electricity_mg, bus_electricity_ng, experiment*):
    Creates point of coupling "pointofcoupling_feedin" for OEM, conversion factor, investment and variable costs for the consumption from the national grid.

* **storage_fix** (*micro_grid_system, bus_electricity_mg, capacity_storage, experiment*):
    Create storage unit "generic_storage" with fixed capacity, variable costs, maximal charge and discharge per timestep,  capacity loss per timestep, charge and discharge efficiency, SOC boundaries (and initial SOC, possibly not needed).

* **storage_oem** (*micro_grid_system, bus_electricity_mg, experiment*):
    Create storage unit "generic_storage" for OEM with investment, variable costs, maximal charge and discharge per timestep,  capacity loss per timestep, charge and discharge efficiency, SOC boundaries (and initial SOC, possibly not needed).

Sinks
------------------------------------------

* **excess** (*micro_grid_system, bus_electricity_mg*):
    Creates sink for excess electricity "sink_excess", eg. if PV panels generate too much electricity.

* **demand** (*micro_grid_system, bus_electricity_mg, demand_profile*):
    Creates demand sink "sink_demand" with fixed flow.

* **feedin** (*micro_grid_system, bus_electricity_ng*):
    Creates sink "sink_feedin" for electricity fed into the national grid. CURRENTLY WITHOUT FEEDIN TARIFF
