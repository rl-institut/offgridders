# Setup
* Install miniconda, cbc solver
* Open Anaconda prompt, create environment
* Run: pip install -r requirements.txt
* Execute: python A_main_script.py

# MicroGridDesignTool_V1.1
* Fixed termination due to undefined 'comments', occurring when simulation without sensitivity analysis is performed
* Added renewable share constraint (testing needed)

# MicroGridDesignTool_V1.0
* Simulation of off- or on-grid energy system (not only MG)
* 1 hr timesteps, 1 to 365 days evaluation time
* All input data via excel sheet
* Easy case definition