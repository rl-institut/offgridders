==========================================
Configuration
==========================================
**to be updated, mostly accurate**

The configuration file enables the user to adapt the simulation to ones need, as listed below. The input file should, however, not be overlooked, as it summarizes all simulation input data and especially enables a sensitivity analysis of a number of parameters. The Input file as well as the sensitivity parameters will be discussed in separate entry.

Coding mode
-----------
To simplify the simulation during coding (speeding up the calculations), **coding_process** can be set to True, shortening the analyzed time frame (_time_start_, _time_end_, _frequency_) and disabling white noise (not coded jet neither for irradiation nor for demand, set in input file with _white_noise_demand_, _white_noise_weather_).::

        coding_process              = True

Restoring results
-----------------
It is possible to resume a sensitivity analysis at the point of interruption by checking::

        restore_oemof_if_existant   = True

Otherwise, all previous results will be deleted and should be manually moved to another folder, if they are to be stored long-term!

For this setting to work, **setting_save_oemofresults** also has to be set to True.

Please keep in mind that the oemof-files are saved with the name of their case and, if present, their sensitivity case. Changing values in the config-file or the input values will therefore will not generate a new oemof-file! When changing settings or values that are not sensitivity values, _restore_oemof_if_existant_ should be disabled to result in a new simulation!.

Simulated cases
---------------
* Base case OEM is by default performed without minimal loading of generators, enabling their sizing. If a minimal loading has to be taken into account, then setting  **base_case_with_min_loading** fixes the generator capacity to the demand peak value (without security margin).::

            base_case_with_min_loading = True


* Checking all operational modes (cases) to be analyzed in **simulated_cases**. A base case OEM to determine necessary capacities is always performed.::

        simulated_cases = {
            'offgrid_fixed': True,            # dispatch with base oem capacities
            'interconnected_buy': True,       # dispatch with interconnected main grid (only consumption)
            'interconnected_buysell': True,   # dispatch with interconnected main grid (consumption+feedin)
            'oem_grid_tied_mg': True,         # optimization of grid-tied mg (consumption+feedin)
            'buyoff': False,                  # NOT IMPLEMENTED
            'parallel': False,                # NOT IMPLEMENTED
            'adapted': False,                 # NOT IMPLEMENTED
        }

Additional settings
___________________
* A sensitivity constraint is added with:::

        include_stability_constraint = True

* Enabling / disabling supply shortage at the project site with **allow_shortage**, especially important when including noise. The maximal share of demand not supplied (shortage) and variable costs can be defined in input_values.py::

        allow_shortage              = False

* If **setting_batch_capacity** is True, then the results of the OEM will be processed in regard to batch capacity sizes. The batch capacities for system components (PV, storage, genset) are defined with _round_to_batch_. The values are always round up to the next batch size (also meaning that an OEM result of 15 kW will be 15kW+batch capacity). If batch capacities are not activated, the dispatch optimization of a micro grid using the OEM capacities can sometimes fail.::

        setting_batch_capacity      = True

In- and output files
____________________
Defining, whether or not input files are to be used for weather (not jet functional) and demand with **use_input_file_demand** and **use_input_file_weather**. If enabled, the file path should be specified with _input_file_demand_ and _input_file_weather_. In input_values.py unit and path of the data in the .csv file have to be specified (_unit_of_input_file_ Wh/kWh) to normalized the values in regards to the energy system, which performs calculations based on kWh.::

        use_input_file_demand       = True
        use_input_file_weather      = False

If no input files are used for demand and weather, the calculated demand and irradiation series can be saved by enabling **write_demand_to_file**, **write_demand_to_file**. The output folder and file prefix (**output_folder** and **output_file**) is defined further below. Notice, that all oemof simulation results are saved in the output folder. The files can be quite numerous, if a sensitivity analysis is performed, but each file is named explicitly after the sensitivity parameters used to generate the results.::

        write_demand_to_file = False
        write_weather_to_file = False
        if use_input_file_demand == True: write_demand_to_file = False
        if use_input_file_weather == True: write_weather_to_file = False

        output_folder='./simulation_results'
        output_file='results'

Display of results and graphs
______________________________
Oemof can generate and save .lp files and .oemof files with the simulation results. These can be saved to the output folder,if **setting_save_lp_file**, **setting_save_oemofresults** are set to True. Especially with long computing times, the oemof results should be saved.::

        setting_save_lp_file        = False
        setting_save_oemofresults   = True

During simulation, a number of graphs can be generated (**display_graphs_solar**, **display_graphs_demand**, **display_graphs_simulation**, **display interrupts computation**) and simulation results printed in the command line (**print_simulation_meta**, **print_simulation_main**, **print_simulation_invest**). If the performed simulation includes a sensitivity analysis, it is advisable to disable all these functions. The details of the simulated case can be displayed with **print_simulation_experiment**.::

        display_graphs_solar        = False
        display_graphs_demand       = False
        display_graphs_simulation   = True
        print_simulation_meta       = False
        print_simulation_main       = False
        print_simulation_invest     = False
        print_simulation_experiment = False

Results saved to csv-file::

        results_demand_characteristics      = True
        results_blackout_characteristics    = True
        results_annuities                   = True
        results_costs                       = True

Oemof settings
______________
In general, the solver of oemof is set to cbc (**solver**). The solver output (**solver_verbose**) is not shown if False.::

        solver = 'cbc'
        solver_verbose = False

To increase computation speed (especially for nonconvex flows in the dispatch OEM), an additional solver option **cmdline_option** is added  with value _cmdline_option_value_. It influences, when the solver accepts the found solution as optimal. Possible options:

* ratioGap
* allowedGap
* mipgap

Comand line options::

        cmdline_option       = 'ratioGap'
        cmdline_option_value = 0.01

The lp file of the energy system analysis with oemof can be saved as well (**setting_lp_file**). When debugging, one should set **debug** to True and limit the analysed timesteps (**coding_process** or even less (ie. 3) timesteps).::

        debug = True


Evaluated timeframe
--------------------
The results (NPV, LCOE, Annuity, fuel consumption) are scaled to **represent the real (annual) values** and are **not** the costs / consumption for the evaluated time period alone (see oemof_general.py)!::


        if coding_process == True:
            evaluated_days          =  1
            time_start              = pd.to_datetime('2018-07-07 0:00', format='%Y-%m-%d %H:%M')
            time_end       = time_start + pd.DateOffset(days=evaluated_days) - pd.DateOffset(hours=1)
            time_frequency          = 'H'

        else:
            evaluated_days          =  1
            time_start              = pd.to_datetime('2018-01-01 0:00', format='%Y-%m-%d %H:%M')
            time_end                = time_start + pd.DateOffset(days=evaluated_days) - pd.DateOffset(hours=1)
            time_frequency          = 'H'

        date_time_index = pd.date_range(start=time_start, end=time_end, freq=time_frequency)

Currently, the tool can ONLY evaluate hourly timesteps.
