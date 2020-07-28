========================
Installation
========================
To set-up oesmot, follow the steps below:

* If python3 is not pre-installed: Install miniconda (`for python 3.7 <https://docs.conda.io/en/latest/miniconda.html>`_)

* Download the `cbc-solver <https://projects.coin-or.org/Cbc>`_ into your system from https://ampl.com/dl/open/cbc/ and integrate it in your system, ie. unzip, place into chosen path, add path to your system variables  (Windows: “System Properties” -->”Advanced”--> “Environment Variables”, requires admin-rights)

* Download latest `oesmot release <https://github.com/smartie2076/simulator_grid-connected_micro_grid/releases>`_

* Open Anaconda prompt, create and activate environment

    `conda create -n [your_env_name] python=3.5`
    `activate [your env_name]`

* Install required packages from requirements.txt file using pip

    `pip install -r requirements.txt`

* Check if requirements were installed with

    `pip list`

* Test your set-up by executing oesmot with the included test-files:

    `python A_main_script.py ./inputs/test_input_template.xlsx`

  This should overwrite the simulation_results/test folder included in your downloaded release. Check for error messages or termination of execution. Delete the folder and execute again to be sure that the tool works.