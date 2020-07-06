"""
Overlying script for tool for the analysis of possible
operational modes of micro grids interconnecting with an unreliable national grid
For efficient iterations? https://docs.python.org/2/library/itertools.html
"""


import pprint as pp
import os, sys
import shutil
from oemof.tools import logger
import logging

import src.A1_general_functions as helpers
import src.B_read_from_files as excel_template
import src.C_sensitivity_experiments as generate_sensitvitiy_experiments
import src.D0_process_input as process_input
import src.E_blackouts_central_grid as central_grid
import src.F_case_definitions as cases
import src.G0_oemof_simulate as oemof_simulate
import src.H0_multicriteria_analysis as multicriteria_analysis

def main():
    # Logging
    logger.define_logging(
        logpath="./",
        logfile="micro_grid_design_logfile.log",
        screen_level=logging.INFO,
        # screen_level=logging.DEBUG,
        file_level=logging.DEBUG,
    )

    logging.info(
        "\n \n Offgridders 3.1"
        "\n Version: 11.10.2019 "
        "\n Coded by: Martha M. Hoffmann "
        "\n Reiner Lemoine Institute (Berlin) \n \n "
    )

    ###############################################################################
    # Get values from excel_template called in terminal                           #
    # python3 A_main_script.py PATH/file.xlsx
    ###############################################################################

    # For compatibility issues: If no key for input file is provided, use generic one input_excel_file
    if len(sys.argv) >= 2:
        test_name_legth = len("tests/tests.py")
        if sys.argv[1][-test_name_legth:] == "tests/tests.py":
            input_excel_file = "./tests/inputs/pytest_test.xlsx"
        else:
            # Own key mentioned for input file
            input_excel_file = str(sys.argv[1])
    else:
        # generic input file
        input_excel_file = "./inputs/test_input_template.xlsx"

    # -------- Get all settings ---------------------------------------------------#
    # General settings, general parameters, sensitivity parameters, project site  #
    # data including timeseries (no noise, not clipped to evaluated timeframe     #
    # -----------------------------------------------------------------------------#

    logging.info('Performing simulations defined by file "' + input_excel_file + '"\n')

    (
        settings,
        parameters_constant_values,
        parameters_sensitivity,
        project_site_s,
        case_definitions,
        multicriteria_data,
    ) = excel_template.process_excel_file(input_excel_file)

    # ---- Define all sensitivity_experiment_s, define result parameters ----------#
    (
        sensitivity_experiment_s,
        blackout_experiment_s,
        overall_results,
        names_sensitivities,
    ) = generate_sensitvitiy_experiments.get(
        settings, parameters_constant_values, parameters_sensitivity, project_site_s
    )

    ###############################################################################
    # Process and initialize                                                      #
    ###############################################################################
    # -------- Generate list of cases analysed in simulation ----------------------#
    case_list = process_input.list_of_cases(case_definitions)

    logging.info(
        "With these cases, a total of "
        + str(settings[TOTAL_NUMBER_OF_EXPERIMENTS] * len(case_list))
        + " simulations will be performed. \n"
    )

    # ----------------- Extend sensitivity_experiment_s----------------------------#
    # with demand, pv_generation_per_kWp, wind_generation_per_kW                  #
    # -----------------------------------------------------------------------------#
    # Adapt timeseries of experiments according to evaluated days
    max_date_time_index, max_evaluated_days = process_input.add_timeseries(
        sensitivity_experiment_s
    )
    settings.update({"max_date_time_index": max_date_time_index})
    settings.update({"max_evaluated_days": max_evaluated_days})

    # -----------Apply noise to timeseries of each experiment --------------------#
    # This results in unique timeseries for each experiment! For comparability    #
    # it would be better to apply noise to each project site. However, if noise   #
    # is subject to sensitivity analysis, this is not possible. To have the same  #
    # noisy timeseries at a project site, noise has to be included in csv data!   #
    # -----------------------------------------------------------------------------#
    # todo test and optionally delete noise function
    process_input.apply_noise(sensitivity_experiment_s) #Applies white noise

    # Calculation of grid_availability with randomized blackouts
    if settings[NECESSITY_FOR_BLACKOUT_TIMESERIES_GENERATION] == True:
        sensitivity_grid_availability, blackout_results = central_grid.get_blackouts(
            settings, blackout_experiment_s
        )

    # ---------------------------- Base case OEM ----------------------------------#
    # Based on demand, pv generation and subjected to sensitivity analysis SOEM   #
    # -----------------------------------------------------------------------------#
    # import all scripts necessary for loop
    experiment_count = 0
    total_number_of_simulations = settings[TOTAL_NUMBER_OF_EXPERIMENTS] * len(
        case_list
    )

    for experiment in sensitivity_experiment_s:

        capacities_oem = {}

        if GRID_AVAILABILITY in sensitivity_experiment_s[experiment].keys():
            logging.debug(
                "Using grid availability as included in timeseries file of project location."
            )
            # grid availability timeseries from file already included in data
        else:
            # extend experiment with blackout timeseries according to blackout parameters
            logging.debug(
                "Using grid availability timeseries that was randomly generated."
            )
            blackout_experiment_name = generate_sensitvitiy_experiments.get_blackout_experiment_name(
                sensitivity_experiment_s[experiment]
            )
            sensitivity_experiment_s[experiment].update(
                {
                    GRID_AVAILABILITY: sensitivity_grid_availability[
                        blackout_experiment_name
                    ]
                }
            )

        ###############################################################################
        # Simulations of all cases                                                    #
        # first the ones defining base capacities, then the others                    #
        ###############################################################################
        for specific_case in case_list:
            # --------get case definition for specific loop------------------------------#
            experiment_case_dict = cases.update_dict(
                capacities_oem,
                case_definitions[specific_case],
                sensitivity_experiment_s[experiment],
            )

            ###############################################################################
            # Creating, simulating and storing micro grid energy systems with oemof       #
            # According to parameters set beforehand                                      #
            ###############################################################################
            experiment_count = experiment_count + 1
            logging.info(
                "Starting simulation of case "
                + specific_case
                + ", "
                + "project site "
                + sensitivity_experiment_s[experiment][PROJECT_SITE_NAME]
                + ", "
                + "experiment no. "
                + str(experiment_count)
                + "/"
                + str(total_number_of_simulations)
                + "..."
            )

            # Run simulation, evaluate results
            oemof_results = oemof_simulate.run(
                sensitivity_experiment_s[experiment], experiment_case_dict
            )

            # Extend base capacities for cases utilizing these values, only valid for specific experiment
            if case_definitions[specific_case][BASED_ON_CASE] == False:
                capacities_oem.update(
                    {
                        experiment_case_dict[
                            CASE_NAME
                        ]: helpers.define_base_capacities(oemof_results)
                    }
                )

            # Extend oemof_results by blackout characteristics
            if GRID_AVAILABILITY in sensitivity_experiment_s[experiment].keys():
                blackout_result = central_grid.oemof_extension_for_blackouts(
                    sensitivity_experiment_s[experiment][GRID_AVAILABILITY]
                )
                oemof_results = central_grid.extend_oemof_results(
                    oemof_results, blackout_result
                )
            else:  # one might check for settings['necessity_for_blackout_timeseries_generation']==True here, but I think its unnecessary
                oemof_results = central_grid.extend_oemof_results(
                    oemof_results, blackout_results[blackout_experiment_name]
                )

            # Extend overall results dataframe with simulation results
            overall_results = helpers.store_result_matrix(
                overall_results, sensitivity_experiment_s[experiment], oemof_results
            )
            # Writing DataFrame with all results to csv file
            overall_results.to_csv(
                sensitivity_experiment_s[experiment][OUTPUT_FOLDER]
                + "/"
                + sensitivity_experiment_s[experiment]["output_file"]
                + ".csv"
            )  # moved from below

            # Estimating simulation time left - more precise for greater number of simulations
            logging.info(
                "    Estimated simulation time left: "
                + str(
                    round(
                        sum(overall_results[EVALUATION_TIME][:])
                        * (total_number_of_simulations - experiment_count)
                        / experiment_count
                        / 60,
                        1,
                    )
                )
                + " minutes."
            )
            print("\n")

        if settings["display_experiment"] == True:
            logging.info("The experiment with following parameters has been analysed:")
            pp.pprint(sensitivity_experiment_s[experiment])

    # display all results
    output_names = [PROJECT_SITE_NAME, CASE]
    output_names.extend(names_sensitivities)
    output_names.extend([LCOE, RES_SHARE])
    logging.info(
        '\n Simulation complete. Resulting parameters saved in "results.csv". \n Overview over results:'
    )
    pp.pprint(overall_results[output_names])

    # Calculate multicriteria analysis
    if settings["perform_multicriteria_analysis"] == True:
        logging.info("Performing multicriteria analysis")
        multicriteria_analysis.main_analysis(
            overall_results, multicriteria_data, settings
        )
        logging.info("Multicriteria analysis was successfully performed")

    logging.shutdown()
    path_from = os.path.abspath("./micro_grid_design_logfile.log")
    path_to = os.path.abspath(
        settings[OUTPUT_FOLDER] + "/micro_grid_design_logfile.log"
    )
    shutil.move(path_from, path_to)

    print(
        "\n Warnings or errors might have occurred. \n"
        + "Please check terminal output or saved log-file to make sure they do not influence your simulation results."
    )
    return 1


if __name__ == "__main__":
    main()
