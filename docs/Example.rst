==========================================
Example: Zambia
==========================================
**This section should be updated**

Following input values are used for simulating Micro Grids in Zambia:

* Demand profile: Profile provided by RLI (min, median, max)

* Weather data: from `https://www.renewables.ninja/ <https://www.renewables.ninja/>`_, country profile of Zambia, land area weighted, MERRA-2

Cost data
---------------------------------------

+++++++++++++++++++++++
General
+++++++++++++++++++++++

According to NREL, 2018, p. 22::

        'price_fuel':                   4.4  USD/gallon
        'combustion_value_fuel':        10  kWh/gallon

Wacc according to Parameter.xlsx from Sarah:::

        'wacc': 12 %

Differing to discount factor of 10% mentioned in NREL, 2018, p. 22.

+++++++++++++++++++++++
PV system
+++++++++++++++++++++++

According to Parameters.xlsx from Sarah:::

        'pv_lifetime':                  20, # not implemented

According to NREL, 2018, p. 22:::

        CAPEX: 800-1200 USD/kWp (DC)

+++++++++++++++++++++++
Storage
+++++++++++++++++++++++

According to Parameters.xlsx from Sarah:::

        'storage_lifetime':             10, # not implemented

Differs from NREL, 2018, p.22 with lifetime of 7 years and roundtrip efficiency of 80%.

+++++++++++++++++++++++
Generators
+++++++++++++++++++++++

According to NREL, 2018, p. 22:::

        CAPEX: 400 USD/kW
        OPEC: 25 USD/kW/a
        Var: 0.023 USD/kWh

According to Parameters.xlsx from Sarah:::

        'genset_lifetime':              10,

Differing: NREL, 2018, p. 22 mentioned minimal loading of 30%.

+++++++++++++++++++++++++++++++++++++++++++++++
Other NOT IMPLEMENTED Components (NREL)
+++++++++++++++++++++++++++++++++++++++++++++++

According to NREL, 2018, p. 22

Charge controller:::

        lifetime: 20 a
        CAPEX:  200-400 USD/kW-DC

Inverter:::

        lifetime: 10 a
        CAPEX:  400-800 USD/kW-DC

Auxiliary (wiring, breakers, protection) for solar and battery:::

        CAPEX:  200-400 USD/kW-DC

Civil costs for solar and battery:::

        CAPEX:  200-400 USD/kW-DC

O&M costs for solar and battery:::

        OPEX: 2% TOTAL CAPEX/a

Distribution network:::

        OPEX: 2% of CAPEX/a
        CAPEX: 200 USD/Household

Soft costs:::

        Project: 1500 USD/kW
        Labour: 3000 USD/a
        Land lease: 800 USD/a

+++++++++++++++++++++++++++++++++++++++++++++++
Other NOT IMPLEMENTED Components (Sarah)
+++++++++++++++++++++++++++++++++++++++++++++++

Soft costs:::

        Project lifetime: 20 a
        Lifetime distribution grid: 40 a

Technical parameters
----------------------

+++++++++++++++++++++++
PV system
+++++++++++++++++++++++

+++++++++++++++++++++++
Storage
+++++++++++++++++++++++

According to Parameters.xlsx from Sarah:::

        'storage_Crate':                1,
        'storage_inflow_efficiency':    0.9,
        'storage_outflow_efficiency':   0.9,
        'storage_capacity_min':         0.2, # from DOD=0.8

Additional assumptions:::

        'storage_capacity_max':         1,
        'storage_loss_timestep':        0,


Genset:::

        'genset_efficiency':            0.58,
        'genset_min_loading':           0,
        'genset_max_loading':           1,

what do I do with rotating mass=40%??

currently no variable efficiency of min = 30%, max =35%

Not used parameters:::

        'price_electricity_main_grid':    0.20,
        'pcoupling_efficiency':            0.58,


Constraints:::

        'max_share_unsupplied_load':    0,
        'costs_var_unsupplied_load':    10,
        'min_res_share':                0,
        'distance_to_grid':             10

Sources:
    * NREL, 2018: [Tariff considerations for micro-grids in Sub-Saharan Africa](https://www.nrel.gov/docs/fy18osti/69044.pdf)