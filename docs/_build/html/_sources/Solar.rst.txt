==========================================
Solar irradiation and pv generation
==========================================

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Option 1: Read from File (OPERATIONAL)
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Option 2: Pure calculation based on pvlib (NOT OPERATIONAL)
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

This setting utilizes the python3 library pvlib to calculate solar irradiation and pv generation. The standard timestep lenght is 15 minutes.

Necessary input values:

* Location (latitude, longitude, altitude, timezone)
* PV module from Sandia lib
* Inverter from Sandia lib
* Constant wind speed and ambient temperature (intermediate)

General: As written in demandlib docs, technical pv module parameters are taken from the sandia-files.

        https://sam.nrel.gov/sites/default/files/sam-library-sandia-modules-2015-6-30.csv
        https://sam.nrel.gov/sites/default/files/sam-library-cec-modules-2015-6-30.csv

Solar irradiation (per sqm) and pv generation (per panel, per kWp) are calculated based on location and a
specific solar module and inverter from the sandia-files. They provide all technical parameters, only
tilt and azimuth are input parameters. Currently working with constant wind speed and ambient temperature.

The solar irradiation as well as the pv generation therefore are highly idealized, and can differ
from the measured local values. The margin should be adressed somewhere in the thesis.

Currently, no white noise taking into account volatile weather conditions is included.
The energy system currently receives the total irradiation as well as the panel generation for the
definition of its components. In the future, multiple panels should be integrated.