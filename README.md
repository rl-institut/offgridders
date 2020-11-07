# Tool description

The simulation tool **Offgridders** * generates a model of an user-defined electricity supply system, optimizes the capacities of the system's generation, storage and electrical components and then performs a dispatch optimization of the optimized capacities.
 
Offgridders is written in python3 and utilizes the Open Energy Modelling Framework ([Website](https://oemof.org/)) ([Code](https://github.com/oemof)) 
and as such uses linerarized component models. 
The electricity system can include AC- as well as DC demand, inverters/rectifiers, 
a connection to a central electricity grid (optional: with blackouts), diesel generator, 
PV panels, wind plant and storage. 
It is possible to allow a defined annual shortage or force a renewable share or system stability constraint. 
For a visualization of the components and demands to be included, 
see the [Readthedocs: Definition of an electricity supply system](https://offgridders.readthedocs.io/en/latest/Definition.html).

Examples for electricity systems that can be simulated with Offgridders: 
* Off-grid micro grid, purely fossil-fuelled or hybridized
* On-grid micro grid, either only consuming or also feeding into the central grid
* Off-grid SHS
* Backup systems (diesel generator, SHS, ...) to ensure reliable supply of consumers connected to weak national grids

If you have questions regarding the tool's execution or it's code pieces, please drop an issue so that as time goes by, I can build an FAQ for offgridders as well as improve its features.

*) previous working name: oesmot - Open Electricity System Modelling and Optimization Tool

# Setup
* Download and integrate cbc solver.
* Open Anaconda prompt, create environment with `python==3.6`
* Run: `pip install -r requirements.txt`
* Execute test data: `python Offgridders.py`
* Run your own simulations by defining the path to your input excel file: `python Offgridders.py ./inputs/test_input_template.xlsx`

When working as a dev, you need to install additional packages with `pip install -r requirements_dev.txt`

For Details: See [Readthedocs: Installation](https://offgridders.readthedocs.io/en/latest/Installation.html)

# Literature

For further reading please refer to [Readthedocs: Literature](https://offgridders.readthedocs.io/en/latest/Literature.html)

# Change log

## MicroGridDesignTool_V3.0
* New excel template - not compatible with previous versions
* Taking into account investments into storage power
* **currently working with oemof 0.2.2**

## MicroGridDesignTool_V2.1
* Error messages
* Bugfix: Working renewable constraint
* Bugfix: Excel-issues with max_shortage=='default' error (from columns='unnamed')

## MicroGridDesignTool_V2.0
Major changes:
* New excel template
* DC and AC bus, connected with inverters/rectifiers, possible AC/DC demand
* Forced battery charge criteria (linearized)
* Minimal renewable share criteria not working!
* Console execution via "python3 A_main_script.py FILE.xlsx"

## MicroGridDesignTool_V1.1
* Fixed termination due to undefined 'comments', occurring when simulation without sensitivity analysis is performed
* New constraint: Renewable share (testing needed)
* Added DC bus including rectifier/inverter (testing needed -> Flows, calculated values)
* Enabled demand AC + demand DC (testing needed -> Flows, calculated values)
* PV charge only through battery can be enabled by not inluding a rectifier (testing needed -> Flows, calculated values)
* New Constraint: Linearized forced charge when national grid available
* New Constraint: Discharge of battery only when maingrid experiences blackout
* New Constraint: Inverter from DC to AC bus only active when blackout occurs

## MicroGridDesignTool_V1.0
* Simulation of off- or on-grid energy system (not only MG)
* 1 hr timesteps, 1 to 365 days evaluation time
* All input data via excel sheet
* Easy case definition

# Open issues
* Timestep lengh 15 Min
* Inlcude generation of network diagram 
* Demand shortage per timestep
