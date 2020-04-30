# Changelog
All notable changes to this project will be documented in this file.

The format is inspired from [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and the versioning aim to respect [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

Here is a template for new release sections

```
## [_._._] - 20XX-MM-DD

### Added
-
### Changed
-
### Removed
-
```
## [Unreleased] 2020-04-01

### Added
- Multi-Criteria Analysis (MCA), a post-processing comparison of the optimization results with H0 and H1
- Plotting bar charts of most relevant criteria
- Calculation of total first time investment costs ("first_investment") and total O&M costs ("operation_mantainance_expenditures")

### Changed
- Changelog.md was updated with old release infos
- requirements.txt: added scipy, xlsxwriter 
- test_input_template.xlsx: Setting whether to perform the multicriteria analysis (MCA) in settings tab; Electricity sales tariff (for MCA only) in case_definitions
- test_input_template.xlsx: New tab "multicriteria_data": weights of dimensions and criteria (all with default values) and which sensibility parameters should be included in the MCA
- A0 to call MCA
- B to read data from xlsx for MCA
- C: Extend set of parameters that are an output of simulation by "total_pv_generation_kWh", "total_wind_generation_kWh", "total_genset_generation_kWh"

### Removed

## Offgridders V3.1.1 [2020-04-01]

Intermediary release, maily focussing on restructuring the code into a code folder and adding a readthedocs.
Readthedocs is still dysfunctional. When starting to use Offgridders, please use release v3.1.

## Offgridders v3.1 [2020-04-01]
Release that includes all changes up to October 2019
- Version that is used for PSBs Cobrador paper + Book chapter
- Version that is used for MMHs Backup system paper

Info: Up to this point, no Changelog.md was in place. Changes will be tracked more carefully starting v4.0

## oesmot v3.0 (22.07.2019)
Working title of tool:
oesmot - Open Electricity System Modelling and Optimization Tool

- New excel template - not compatible with previous versions
- Taking into account investments into storage power
Remark: Currently working with oemof 0.2.2

Features:
- AC- and DC-bus, allowing AC- and DC-demand, connected through inverter/rectifier
- DC-side: Storage, PV panels
- AC-side: Wind plant, diesel generator, transformer station to (weak) central grid
- All inputs defined through excel input sheet
- Supported: Sensitivity analysis and definition of multiple electricity systems at once
- Supports constraints: Renewable share constraint, stability constraints (3 versions), max. allowed shortage
- Outputs saved in csv, automatic generation of electricity flow graphs
- Error messages & warnings


## MicroGridDesignTool_V2.1
- Error messages
- Bugfix: Working renewable constraint
- Bugfix: Excel-issues with max_shortage=='default' error (from columns='unnamed')

## MicroGridDesignTool_V2.0
Major changes:
- New excel template
- DC and AC bus, connected with inverters/rectifiers, possible AC/DC demand
- Forced battery charge criteria (linearized)
- Minimal renewable share criteria not working!
- Console execution via "python3 A_main_script.py FILE.xlsx"

## MicroGridDesignTool_V1.1
- Fixed termination due to undefined 'comments', occurring when simulation without sensitivity analysis is performed
- New constraint: Renewable share (testing needed)
- Added DC bus including rectifier/inverter (testing needed -> Flows, calculated values)
- Enabled demand AC + demand DC (testing needed -> Flows, calculated values)
- PV charge only through battery can be enabled by not inluding a rectifier (testing needed -> Flows, calculated values)
- New Constraint: Linearized forced charge when national grid available
- New Constraint: Discharge of battery only when maingrid experiences blackout
- New Constraint: Inverter from DC to AC bus only active when blackout occurs

## MicroGridDesignTool_V1.0
- Simulation of off- or on-grid energy system (not only MG)
- 1 hr timesteps, 1 to 365 days evaluation time
- All input data via excel sheet
- Easy case definition


