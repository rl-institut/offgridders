==========================================
Input values
==========================================
**to be updated, mostly accurate**

TThere are numerous input values that have to be provided for the model. Most of those can be defined either as a constant value (_sensitivity_constants_)::

        sensitivity_constants = {'variable_name':  constant value}

or as an interval (_sensitivity_bounds_), thus being subject of the sensitivity analysis:::

        sensitivity_bounds = {'variable_name':
            {'min': min_value, 'max': max_value, 'step': steplenght}}

Costs and prices
----------------
While prices and related factors can be defined directly::

        'price_fuel':                   10    # /unit
        'combustion_value_fuel':        9.41  # kWh/unit
        'wacc':                         0.12  # factor
        'project_life':                 20    # a

Component costs are defined using above _wacc_ (used as discounting factor) as well as the investment costs (first time price of component per unit), the fixed annual operational costs (eg. operation and maintenance), the variable costs per kWh (eg. wear) and the components lifetime. While not explicitly implemented, one could try to put a economic value to the kWh-throughput of batteries to mirror their wear better than with the simplification of a constant lifetime.

Additional costs:::

         'project_cost_fix':    0  # -
         'project_cost_opex':   0  # /a

The distribution grid costs should be mentioned separately from the project costs to allow for certain operation modes (cases):::

         'distribution_grid_cost_investment': 0,  #
         'distribution_grid_cost_opex':      50,  # /a
         'distribution_grid_lifetime':       40,  #

Constraints
-----------
If the stability constraint is activated in the `simulation settings <https://github.com/smartie2076/simulator_grid-connected_micro_grid/wiki/Configuration-file>`_, the stability limit in terms of minimal share of demand that the system should be able to meet in case of volatilities by fossil-fuelled generation or battery discharge has to be defined:::

        'stability_limit':     0.5 # factor of demand

Same goes for allowed demand shortage (a setting in the config-file): define the boundaries of the shortage an enumerate the shortage.::

        'max_share_unsupplied_load':    0   # factor
        'costs_var_unsupplied_load':    10  # /kWh

The minimal renewable factor can currently only be defined for off-grid micro grids: The boundary is only included in the fuel source, while electricity consumed from the main grid would also have to be counted as non-renewable energy (at least partly).::

        'min_renewable_share':                0   # factor

Main grid::

        'maingrid_distance':                   10     # km
        'maingrid_extension_cost_investment':  15000  # /km
        'maingrid_extension_cost_opex':        0      # /km/a
        'maingrid_extension_lifetime':         0      # /km/a
        'maingrid_renewable_share':            0      # factor
        'maingrid_electricity_price':          0.20   # /unit
        'maingrid_feedin_tariff':              0.12   # /unit

Blackouts::

        'blackout_duration':                2  # hrs per blackout
        'blackout_duration_std_deviation'   0  # While programming
        'blackout_frequency':               7  # blackouts per month
        'blackout_frequency_std_deviation'  0  # While programming

Storage::

        'storage_capacity_max':        1     # factor
        'storage_capacity_min':        0.2   # factor (1-DOD)
        'storage_cost_investment':     800   # /unit
        'storage_cost_opex':           0     # /unit/a
        'storage_cost_var':            0     # /kWh
        'storage_Crate':               1 	  # factor
        'storage_inflow_efficiency':   0.9   # factor
        'storage_initial_soc':         None  # None or factor
        'storage_lifetime':            6     # a
        'storage_loss_timestep':       0     # factor
        'storage_outflow_efficiency':  0.9   # factor

Fossil-fueled generator::

        'genset_cost_investment':      800    # /unit
        'genset_cost_opex':            25     # /unit/a
        'genset_cost_var':             0.023  # /kWh
        'genset_efficiency':           0.33   # factor
        'genset_lifetime':             10     # a
        'genset_max_loading':          1      # factor
        'genset_min_loading':          0      # factor

PV System::

        'pv_cost_investment':      950  # /unit
        'pv_cost_opex':            0    # /unit/a
        'pv_cost_var':             0    # /kWh
        'pv_lifetime':             20   # a

The PV system generation per kWp be based on a calculation with pvlib or can be provided by input parameters. The definition is not part of the dictionary list of simulation parameters.

Pure calculation
----------------
The pv system generation per kWp can be calculated based on Location::

        location_name = 'Berlin'
        latitude = 50
        longitude = 10
        altitude = 34
        timezone = 'Etc/GMT-1'

and PV and inverter specifications. The specific module and inverter used can be chosen from the SANDIA list and already includes all technical parameters.::

        pv_composite_name = 'basic'
        surface_azimuth = 180
        tilt = 0
        module_name = 'Canadian_Solar_CS5P_220M___2009_'
        inverter_name = 'ABB__MICRO_0_25_I_OUTD_US_208_208V__CEC_2014_'

++++++++++++++++++++++++++++++++++++++++++
Using input data (NOT IMPLEMENTED)
++++++++++++++++++++++++++++++++++++++++++

Alternatively, PV irradiation data, temperature coefficient and panel efficiency can be loaded.::

        weatherfile = 'weather.csv' # including...???
        pv_efficiency = 0.16
        pv_temperature_coefficient = -0.04


++++++++++++++++++++++++++++++++++++++++++
Point of Coupling (NOT IMPLEMENTED)
++++++++++++++++++++++++++++++++++++++++++

Point of coupling::

        'pcoupling_cost_investment':   1500   # /unit
        'pcoupling_cost_opex':         0      # /unit/a
        'pcoupling_cost_var':          0      # /kWh
        'pcoupling_efficiency':        0.98   # factor
        'pcoupling_lifetime':          20     # a