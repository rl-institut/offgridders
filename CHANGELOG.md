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

### Fixed
-
```

## [Unreleased]

### Added
- Version number with `src/version.py` (#150)
- Constant variables in `constants.py`: `INPUT_TEMPLATE_EXCEL_XLSX`(#150), `GENSET_HOURS_OF_OPERATION` (#153)
- Added pytests for `D1.crf` and `D1.present_value_of_changing_fuel_price` (#153)
- Implement new KPI: `GENSET_HOURS_OF_OPERATION` with new function `G3.get_hours_of_operation()` for generator evaluation, including pytests (#153)

### Changed
- Execute all pytests in Travis `.travis.yml` (#150)
- Added version number to `setup.py` (#150)
- Moved `main()` from `Offgridders.py` to new file `src/cli.py` (#150)
- Enable benchmark tests for Offgridders: Add optional argument `input_file` to `main()` (#150)
- Added `GENSET_HOURS_OF_OPERATION` in `C1.overall_results_title` (#153)
- Updated 'requirements.txt' (#164, #167)
- Fix deprecation warnings for pandas (#167)
### Removed
-

### Fixed
- Basic pytest to ensure no termination with test input file (`tests/inputs/pytest_test.xlsx`) (#150)
- `present_value_of_changing_fuel_price` now correctly calculated, fixed function call of `D1.present_value_of_changing_fuel_price` in `D0` (#153)

## [Offgridders V4.6.1] - 2020-11-07

### Added
- Docstrings to A1, B, C, D0, D1, E, F, G0-2 (#131, #132, #133, #134, #135, #136)
- Literature file to readthedocs (#129)
- Added some docstrings to functions in `G2a`, copied from `Components.rst` (#125)
- Replaced "Yes" and "No" with True and False. In H0 and inside the Excel Files (#127)

### Changed
- Update README (#129)
- Bump `black` version number (#144)
- Devided the `requirements.txt` into a base one (users) and an extended one for developers and for troubleshooting (`requirements_dev.txt`) (#145)
- Updated the installation instructions in `Readme.md` and of the RTD (#145)

### Fixed
- Small content corrections to readthedocs (#119,#123,#125)
- Fixed parsing issue with `evaluation_prespective` by fixing definition of logging message and constant varibale definition of `AC_SYSTEM` (#143)
 
## [Offgridders V4.6] - 2020-08-17

### Changed
- Replaced `== False` with `is False` and `== True` with `is True`
- Facilitated upgrade to unbundled oemof version: `oemof.solph == 0.4.0`, `oemof.network==0.4.0rc0`, `oemof.tools==0.4.0` and update `requirements.txt`

## [Offgridders V4.5] - 2020-08-12

### Added
- Constant variables for strings are gathered in `constants.py` (#89,#117, #118)

### Changed
- Replaced parameter strings with variable calls  (#89,#117, #118)
- Changed path calls to `os.path.join` to enable compatability (#118)
- Log messages now call variable of parameter name (#117, #118)

### Removed
- Try/Except clauses at module import (#103) 

### Fixed
-

## [Offgridders V4.4] - 2020-07-09

### Added
- Error message if parameter `evaluation_perspective` is not chosen correctly (#97)
- Warning message if `fuel_price_change_annual` != 0, as calculation may be faulty (#97)

### Changed
- Added parameter `consumption_fuel_annual_kWh` to simulation outputs (#97)
- Input template file so that it runs MCA and gives options of `evaluation_perspective` (#97)
- If `fuel_price_change_annual` == 0, function `present_value_changing_fuel_price` is not executed and returns fuel price (#97)
- Order of cost results in simulation outputs, as `first_investment_cost`, `operation_mantainance_expenditures` as these are not to be added to costs, expenditures and revenues to calculate the NPC (#97)
- Formula calculating the residual value of an asset. Now, the sales revenue is translated into a present value: 
`linear_depreciation_last_investment = last_investment / lifetime` and `capex = capex - linear_depreciation_last_investment * (number_of_investments * lifetime - project_life) / (1 + wacc) ** (project_life)` (#97)
                )`
### Removed
- Removed unused function call in G2a (`genset_oem_minload`) (#97)

### Fixed
- Miscalculation of `total_demand_supplied_annual_kWh` due to wrong `evaluation_perspective` on tab `case_definitions`  (#97)
- Function call of `present_value_changing_fuel_price` (#97)
- Typo: Replace `operation_mantainance_expenditures` by `operation_maintenance_expenditures` (#97)

## [Offgridders V4.3] - 2020-07-02

### Fixed
- Faulty function calls from module structure change: 'get_universal_parameters',
'get_combinations_around_base', 'get_number_of_blackouts' (#86)

## [Offgridders V4.2] - 2020-06-30

### Added
- `total_excess_annual_kWh` to list of output parameters. Calculation: `total_excess_annual_kWh = total_excess_ac_annual_kWh + total_excess_dc_annual` (#73)
- Optional parameters and their default values `fuel_co2_emission_factor` (2.68 kgCO2eq/l diesel) and `maingrid_co2_emission_factor` (0.9 kgCO2eq/kWh) to input template, sheet `input_constant` and module `B` (#77)
- Calculation of C02 emissions and new output value: `co2_emissions_kgCO2eq`. It is based on the kWh consumption from the national grid (before transfromer station losses) and diesel consumption (#77)

### Changed
-

### Removed
-

### Fixed
- Typo when calling for the inverter capacity ('capacity_inverter_dc_ac_kW' and not 'capacity_inverter_kW'), (#75)
- Typo for unit of `maingrid_extension_lifetime` (a)

## [Offgridders V4.1] - 2020-06-30

### Added
- readthedocs.yml file (#59)

### Changed
- Moved Wiki to Readthedocs (#41)
- Changed class structure to modules/functions (#53)
- Script A0 was refactored to Offgridders. It runs now through `python Offgridders.py YOUR_INPUT_EXCEL_SHEET_PATH` (#53)

### Fixed
- Compilation of readthedocs by changing advanced settings on readthedocs.io (#59)

## [Offgridders V4.0] 2020-04-30

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
