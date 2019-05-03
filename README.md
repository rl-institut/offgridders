# Setup
* Install miniconda, cbc solver
* Open Anaconda prompt, create environment
* Run: pip install -r requirements.txt
* Execute: python A_main_script.py

# MicroGridDesignTool_V1.1
* Fixed termination due to undefined 'comments', occurring when simulation without sensitivity analysis is performed
* New constraint: Renewable share (testing needed)
* Added DC bus including rectifier/inverter (testing needed -> Flows, calculated values)
* Enabled demand AC + demand DC (testing needed -> Flows, calculated values)
* PV charge only through battery can be enabled by not inluding a rectifier (testing needed -> Flows, calculated values)
* New Constraint: Linearized forced charge when national grid available
* New Constraint: Discharge of battery only when maingrid experiences blackout
* New Constraint: Inverter from DC to AC bus only active when blackout occurs

# MicroGridDesignTool_V1.0
* Simulation of off- or on-grid energy system (not only MG)
* 1 hr timesteps, 1 to 365 days evaluation time
* All input data via excel sheet
* Easy case definition

# Open issues
* Timestep lengh 15 Min
* Look into swarm grid definition - execute simulation with python A_main_script.py file.xlsx
* Inlcude network diagram thingy
* Demand shortage per timestep!
* check res/stability constraint on whether or not previous things are fullfilled -> shouldnt this be not working now? 
or is it only limiting shortage on AC bus, but not DC bus?
* integrate shortage per timestep criterion