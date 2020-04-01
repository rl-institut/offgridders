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
- requirements.txt: added scipy, xlsxwriter 
- test_input_template.xlsx: Setting whether to perform the multicriteria analysis (MCA) in settings tab; Electricity sales tariff (for MCA only) in case_definitions
- test_input_template.xlsx: New tab "multicriteria_data": weights of dimensions and criteria (all with default values) and which sensibility parameters should be included in the MCA
- A0 to call MCA
- B to read data from xlsx for MCA
- C: Extend set of parameters that are an output of simulation by "total_pv_generation_kWh", "total_wind_generation_kWh", "total_genset_generation_kWh"

### Removed


