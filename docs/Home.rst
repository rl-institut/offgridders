========================
Home
========================

*Welcome to the simulator_grid-connected_micro_grid wiki!*

**Offgridders**, based on python3, simulates an user-defined electricity supply system and performs an optimization of the system's capacities as well as a dispatch-optimization of the optimized assets, utilizing the Open Energy Modelling Framework ([Website](https://oemof.org/)) ([Code](https://github.com/oemof)). The system can be defined using:

* AC- and DC-demand
* Inverters and rectifiers connecting AC- and DC-bus
* Electricity storage system
* PV panels
* Wind plant
* Diesel generator
* Connection to a central electricity grid (optional: intermittent blackouts)
* Contraints: supply shortage, renewable share, stability constraint

A detailed description of all components defining an electricity system in oesmot is provided in [github wiki: Definition of an electricity supply system](https://github.com/smartie2076/simulator_grid-connected_micro_grid/wiki/Definition-of-an-electricity-supply-system). Based on these components,
exemplary electricity systems that can be simulated are:

* Fossil-fuelled micro grid
* Hybridized micro grid, utilizing PV, wind and/or storage
* Off- as well as on-grid micro grid
* Standalone solutions with low capacity (eg. SHS)
* Backup electricity supply systems ensuring reliable supply of consumers connected to weak grids

A description of these different electricity systems is provided in [github wiki: Exemplary electricity supply systems](https://github.com/smartie2076/simulator_grid-connected_micro_grid/wiki/Exemplary-electricity-supply-systems).

For setting-up oesmot on your operating system, please check the [github wiki: Installation](https://github.com/smartie2076/simulator_grid-connected_micro_grid/wiki/Installation).

# Features of oesmot
The features of the simulation tool can be summarized with:

* **Versatile application and scenario definition**. Through scenario definitions, a
multitude of energy system models (cases) can be defined. The energy system model’s
capacity and their dispatch are optimized. All energy systems can be simulated that
can be reduced to a combination of the following components: AC and/or DC demand,
generator, photovoltaic (PV) panels, storage, inverters, rectifiers, wind plant and connection to a national grid.

* **User-friendly interface**. All simulation parameters, project locations and scenarios
can be defined within a single excel file (see [github wiki: **Configurations**](https://github.com/smartie2076/simulator_grid-connected_micro_grid/wiki/Configuration-file)). The time series connected to one or multiple project locations can be defined in one or multiple .csv file(s). Even though it
is necessary to install Python as well as required packages and execute the tool via a
command-line interface (e.g. miniconda), this should enable users without programming
experience to use the tool without having to edit any of the provided code.

* **Multitude of input parameters, sensitivity analysis**. Numerous parameters can
be defined to characterize the electricity solution to be simulated, including many
techno-economical parameters (see [github wiki: Input parameters](https://github.com/smartie2076/simulator_grid-connected_micro_grid/wiki/Input-values)). A sensitivity analysis of any parameter can evaluate its influence on the overall optimization results. The simulation can run for any time
period between one day and a year with hourly time steps.

* **Multiple project sites**. Multiple locations with specific time series, e.g. AC or
DC demand, renewable generation and grid availability can be defined in the excel
template. A location-specific definition of input parameters is possible.

* **Restarting simulations**. Oemof results as well as generated grid availability time
series can be saved and used to restart simulations, e.g. if a simulation aborts. This
can, especially during a multi-parameter sensitivity analysis, save computing time.

* **Automatically generated graphs**. To visualize the dispatch of the optimized components, it is possible to generate and save graphs displaying the storage’s charging
process and more importantly the electricity flows, SOC and grid availability of the
system. They can be saved as .png files displaying the whole analyzed time period as
well as five exemplary days and as time series in .csv files.

* **Output of linear equation system**. Advanced users can save the linear equation
system generated through oemof, e.g. to check its validity or solve the equation system
with other solvers suitable for Pyomo.

* **Additional constraints**. To ensure technological reliability of the system, a static
stability constraint can be applied. A minimal renewable share can also be required.

* **Fast computation**. A capacity and dispatch optimization takes 40 +/-5 seconds for a year with hourly values.

This description is largely based upon the methodology chapter of Martha Hoffmann's master thesis:

* Martha M. Hoffmann: Optimizing the Design of Off-Grid Micro Grids Facing Interconnection with an Unreliable Central Grid Utilizing an Open-Source Simulation Tool, June 2019, Reiner Lemoine Institut and Technologische Universität Berlin
