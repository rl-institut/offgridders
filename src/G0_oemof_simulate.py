"""
Overlying script for tool for the analysis of possible
operational modes of micro grids interconnecting with an unreliable national grid

General settings, simulation-specific input data taken from dictionary experiment

Utilizing the bus/component library oemof_generatemodel and the process oemof library oemof_general
new cases can easily be added.
"""

# to check for files and paths
import os.path
import timeit

# Logging of info
import logging
import oemof.outputlib as outputlib

# For speeding up lp_files and bus/component definition in oemof as well as processing
import src.G1_oemof_create_model as oemof_model
import src.G2b_constraints_custom as constraints_custom
import src.G3_oemof_evaluate as timeseries
import src.G3a_economic_evaluation as economic_evaluation
import src.G3b_plausability_tests as plausability_tests
import src.G4_output_functions as output

# This is not really a necessary class, as the whole experiement could be given to the function, but it ensures, that
# only correct input data is included

def run(experiment, case_dict):
        """
        Funktion to generate oemof-lp file, simulate and extract simulation results from oemof-results,
        including extraction of time series, accumulated values, optimized capacities.
        Simulation results are extracted based on their case definitions in case_dict,
        thus the only part where changes are neccesary to modify cases is not here but
        in the case definitions directly (oemof_cases). If the computation of the extracted
        results itself should change (eg. in the future allowing a finer timestep resulution),
        this is the right place.
        """
        start = timeit.default_timer()

        file_name = case_dict[FILENAME]

        # For restoring .oemof results if that is possible (speeding up computation time)
        if (
            os.path.isfile(
                experiment[OUTPUT_FOLDER] + "/oemof/" + file_name + ".oemof"
            )
            and experiment[RESTORE_OEMOF_IF_EXISTENT] == True
        ):
            logging.info("Previous results of " + case_dict[CASE_NAME] + " restored.")

        # If .oemof results do not already exist, start oemof-process
        else:
            # generate model
            micro_grid_system, model = oemof_model.build(experiment, case_dict)
            # perform simulation
            micro_grid_system = oemof_model.simulate(
                experiment, micro_grid_system, model, file_name
            )
            # store simulation results to .oemof
            oemof_model.store_results(
                micro_grid_system, file_name, experiment[OUTPUT_FOLDER]
            )

        # it actually is not really necessary to restore just simulated results... but for consistency and to make sure that calling results is easy, this is used nevertheless
        # load oemof results from previous or just finished simulation
        micro_grid_system = oemof_model.load_oemof_results(
            experiment[OUTPUT_FOLDER], file_name
        )

        # output.save_network_graph(micro_grid_system, case_dict['case_name'])
        ######################
        # Processing
        ######################
        results = micro_grid_system.results[MAIN]
        meta = micro_grid_system.results[META]

        oemof_results = {
            CASE: case_dict[CASE_NAME],
            FILENAME: "results_" + case_dict[CASE_NAME] + experiment[FILENAME],
            OBJECTIVE_VALUE: meta[OBJECTIVE],
            SIMULATION_TIME: meta[SOLVER][TIME],
            COMMENTS: experiment[COMMENTS],
        }

        electricity_bus_ac = outputlib.views.node(results, BUS_ELECTRICITY_AC)

        electricity_bus_dc = outputlib.views.node(results, BUS_ELECTRICITY_DC)

        try:

            e_flows_df = timeseries.get_demand(
                case_dict,
                oemof_results,
                electricity_bus_ac,
                electricity_bus_dc,
                experiment,
            )
            e_flows_df = timeseries.get_shortage(
                case_dict,
                oemof_results,
                electricity_bus_ac,
                electricity_bus_dc,
                experiment,
                e_flows_df,
            )

            oemof_results.update(
                {
                    SUPPLY_RELIABILITY_KWH: oemof_results[
                        TOTAL_DEMAND_SUPPLIED_ANNUAL_KWH
                    ]
                    / oemof_results[TOTAL_DEMAND_ANNUAL_KWH]
                }
            )

            e_flows_df = timeseries.get_excess(
                case_dict,
                oemof_results,
                electricity_bus_ac,
                electricity_bus_dc,
                e_flows_df,
            )

            timeseries.get_fuel(case_dict, oemof_results, results)
            e_flows_df = timeseries.get_genset(
                case_dict, oemof_results, electricity_bus_ac, e_flows_df
            )

            e_flows_df = timeseries.get_national_grid(
                case_dict,
                oemof_results,
                results,
                e_flows_df,
                experiment[GRID_AVAILABILITY],
            )

            e_flows_df = timeseries.get_wind(
                case_dict,
                oemof_results,
                electricity_bus_ac,
                e_flows_df,
                experiment[PEAK_WIND_GENERATION_PER_KW],
            )

            e_flows_df = timeseries.get_pv(
                case_dict,
                oemof_results,
                electricity_bus_dc,
                experiment,
                e_flows_df,
                experiment[PEAK_PV_GENERATION_PER_KWP],
            )

            e_flows_df = timeseries.get_storage(
                case_dict, oemof_results, experiment, results, e_flows_df
            )

            e_flows_df = timeseries.get_rectifier(
                case_dict,
                oemof_results,
                electricity_bus_ac,
                electricity_bus_dc,
                e_flows_df,
            )

            e_flows_df = timeseries.get_inverter(
                case_dict,
                oemof_results,
                electricity_bus_ac,
                electricity_bus_dc,
                e_flows_df,
            )

            # determine renewable share of system - not of demand, but of total generation + consumption.
            timeseries.get_res_share(case_dict, oemof_results, experiment)

        except (KeyError):
            logging.error(
                "Optimized values for a component could not be found in simulation results. \n"
                "Did you use restore_oemof_if_existant=True? Than you probably reload an out-dated model and its results."
            )

        # Run plausability test on energy flows
        plausability_tests.run(oemof_results, e_flows_df)

        # Run test on oemof constraints
        if case_dict[STABILITY_CONSTRAINT] == False:
            pass
        elif case_dict[STABILITY_CONSTRAINT] == SHARE_BACKUP:
            constraints_custom.backup_test(
                case_dict, oemof_results, experiment, e_flows_df
            )
        elif case_dict[STABILITY_CONSTRAINT] == "share_usage":
            constraints_custom.usage_test(
                case_dict, oemof_results, experiment, e_flows_df
            )
        elif case_dict[STABILITY_CONSTRAINT] == "share_hybrid":
            constraints_custom.hybrid_test(
                case_dict, oemof_results, experiment, e_flows_df
            )

        constraints_custom.share_test(case_dict, oemof_results, experiment)
        constraints_custom.forced_charge_test(
            case_dict, oemof_results, experiment, e_flows_df
        )
        constraints_custom.discharge_only_at_blackout_test(
            case_dict, oemof_results, e_flows_df
        )
        constraints_custom.inverter_only_at_blackout_test(case_dict, oemof_results, e_flows_df)

        # Generate output (csv, png) for energy/storage flows
        output.save_mg_flows(experiment, case_dict, e_flows_df, experiment[FILENAME])
        output.save_storage(experiment, case_dict, e_flows_df, experiment[FILENAME])

        # print meta/main results in command window
        if electricity_bus_ac != None:
            output.print_oemof_meta_main_invest(
                experiment, meta, electricity_bus_ac, case_dict[CASE_NAME]
            )
        if electricity_bus_dc != None:
            output.print_oemof_meta_main_invest(
                experiment, meta, electricity_bus_dc, case_dict[CASE_NAME]
            )

        # Evaluate simulated systems regarding costs
        economic_evaluation.project_annuities(case_dict, oemof_results, experiment)

        duration = timeit.default_timer() - start
        oemof_results.update({EVALUATION_TIME: round(duration, 5)})

        # Infos on simulation
        logging.info(
            'Simulation of case "'
            + case_dict[CASE_NAME]
            + '" resulted in : \n'
            + "    "
            + "  "
            + "    "
            + "    "
            + "    "
            + str(round(oemof_results[LCOE], 3))
            + " currency/kWh, "
            + "at a renewable share of "
            + str(round(oemof_results[RES_SHARE] * 100, 2))
            + " percent"
            + " with a reliability of "
            + str(round(oemof_results[SUPPLY_RELIABILITY_KWH] * 100, 2))
            + " percent"
        )
        logging.info(
            "    Initial simulation time (s): "
            + str(round(oemof_results[SIMULATION_TIME], 2))
            + " / Actual evaluation time (s): "
            + str(round(duration, 2))
        )

        # Debug messages
        logging.debug(
            '    Exact OEM results of case "'
            + case_dict[CASE_NAME]
            + '" : \n'
            + "    "
            + "  "
            + "    "
            + "    "
            + "    "
            + str(round(oemof_results[CAPACITY_STORAGE_KWH], 3))
            + " kWh battery, "
            + str(round(oemof_results[CAPACITY_PV_KWP], 3))
            + " kWp PV, "
            + str(round(oemof_results[CAPACITY_WIND_KW], 3))
            + " kW wind, "
            + str(round(oemof_results[CAPACITY_GENSET_KW], 3))
            + " kW genset "
            + "at a renewable share of "
            + str(round(oemof_results[RES_SHARE] * 100, 2))
            + " percent"
            + " with a reliability of "
            + str(round(oemof_results[SUPPLY_RELIABILITY_KWH] * 100, 2))
            + " percent"
        )
        logging.debug("    Simulation of case " + case_dict[CASE_NAME] + " complete.")
        logging.debug("\n")

        if experiment["save_oemofresults"] == False:
            os.remove(experiment[OUTPUT_FOLDER] + "/oemof/" + file_name + ".oemof")

        return oemof_results
