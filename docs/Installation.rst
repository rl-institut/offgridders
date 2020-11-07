============
Installation
============
To set-up Offgridders, follow the steps below:

* If python3 is not pre-installed: Install miniconda (`for python 3.7 <https://docs.conda.io/en/latest/miniconda.html>`_)

* Download the `cbc-solver <https://projects.coin-or.org/Cbc>`_ into your system from https://ampl.com/dl/open/cbc/ and integrate it in your system, ie. unzip, place into chosen path, add path to your system variables  (Windows: “System Properties” -->”Advanced”--> “Environment Variables”, requires admin-rights). If you do not have the necessary rights to define a `PATH` variable, you can place `cbc.exe` directly into your project (same folder as `Offgridders.py`).

* Download latest `Offgridders release <https://github.com/rl-institut/offgridders>`_

* Open Anaconda prompt, create and activate an environment. You need to use `python==3.6` or `python==3.7`.

    `conda create -n [your_env_name] python=3.6`
    `activate [your env_name]`

* Install required packages from requirements.txt file using pip

    `pip install -r requirements.txt`

* Check if requirements were installed with

    `pip list`

* Test your set-up by executing Offgridders with the included test-files:

    `python Offgridders.py`

  This should overwrite the simulation_results/test folder included in your downloaded release. Check for error messages or termination of execution. Delete the folder and execute again to be sure that the tool works.

* Run own simulations by specifying the input folder:

    `python Offgridders.py ./inputs/test_input_template.xlsx`

* For developers, you need to install additional requirements with:

    `pip install -r requirements_dev.txt`


Troubleshooting
###############

If you experience troubles with the compatibility of installed packages, try installing the requirements `requirements_dev.txt`. They may specify the package versions that colloborate well together.