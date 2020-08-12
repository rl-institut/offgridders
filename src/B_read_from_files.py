import pandas as pd
import logging
import os
import sys
import shutil

from src.constants import (
    SETTINGS,
    INPUT_CONSTANT,
    INPUT_SENSITIVITY,
    PROJECT_SITES,
    CASE_DEFINITIONS,
    MULTICRITERIA_DATA,
    INPUT_FOLDER_TIMESERIES,
    TIMESERIES_FILE,
    TITLE_GRID_AVAILABILITY,
    NECESSITY_FOR_BLACKOUT_TIMESERIES_GENERATION,
    SETTING_VALUE,
    UNIT,
    VALUE,
    CASE_NAME,
    MAX_SHORTAGE,
    NUMBER_OF_EQUAL_GENERATORS,
    DIMENSIONS,
    CRITERIA,
    PARAMETERS,
    TARIFF,
    TITLE_TIME,
    TITLE_DEMAND_AC,
    TITLE_DEMAND_DC,
    TITLE_PV,
    TITLE_WIND,
    DEMAND_AC,
    DEMAND_DC,
    PV_GENERATION_PER_KWP,
    WIND_GENERATION_PER_KW,
    GRID_AVAILABILITY,
    OUTPUT_FOLDER,
    RESTORE_OEMOF_IF_EXISTENT,
    RESTORE_BLACKOUTS_IF_EXISTENT,
    SAVE_LP_FILE,
    LP_FILE_FOR_ONLY_3_TIMESTEPS,
    SAVE_TO_CSV_FLOWS_STORAGE,
    SAVE_TO_PNG_FLOWS_STORAGE,
    SAVE_TO_CSV_FLOWS_ELECTRICITY_MG,
    SAVE_TO_PNG_FLOWS_ELECTRICITY_MG,
    FILE_INDEX,
    EVALUATION_PERSPECTIVE,
    DEFAULT,
    AC_SYSTEM,
    DC_SYSTEM,
    SEPARATOR,
    GRID_AVAILABILITY_CSV,
    FUEL_CO2_EMISSION_FACTOR,
    MAINGRID_CO2_EMISSION_FACTOR,
    INPUT_TEMPLATE_EXCEL_XLSX,
    OEMOF_FOLDER,
    INPUTS_FOLDER,
    ELECTRICITY_MG_FOLDER,
    STORAGE_FOLDER,
    LP_FILES_FOLDER,
)

# requires xlrd


def process_excel_file(input_excel_file):
    #######################################
    # Reads all input from excel template #
    #######################################

    # Name of tabs
    sheet_settings = SETTINGS
    sheet_input_constant = INPUT_CONSTANT
    sheet_input_sensitivity = INPUT_SENSITIVITY
    sheet_project_sites = PROJECT_SITES
    sheet_case_definitions = CASE_DEFINITIONS
    sheet_multicriteria_data = MULTICRITERIA_DATA

    settings = get_settings(input_excel_file, sheet_settings)

    # -------- Check for, create or empty results directory -----------------------#
    check_output_directory(settings, input_excel_file)

    (parameters_constant_units, parameters_constant_values,) = get_parameters_constant(
        input_excel_file, sheet_input_constant
    )
    parameters_sensitivity = get_parameters_sensitivity(
        input_excel_file, sheet_input_sensitivity
    )

    project_site_s = get_project_sites(input_excel_file, sheet_project_sites)

    necessity_for_blackout_timeseries_generation = False
    # extend by timeseries
    for project_site in project_site_s:
        # copy input timeseries to new location
        path_from = os.path.abspath(
            settings[INPUT_FOLDER_TIMESERIES]
            + "/"
            + project_site_s[project_site][TIMESERIES_FILE]
        )
        path_to = os.path.abspath(
            settings[OUTPUT_FOLDER]
            + "/inputs/"
            + project_site_s[project_site][TIMESERIES_FILE]
        )
        shutil.copy(path_from, path_to)

        from_file(project_site_s[project_site], path_from)
        if project_site_s[project_site][TITLE_GRID_AVAILABILITY] == "None":
            necessity_for_blackout_timeseries_generation = True

    settings.update(
        {
            NECESSITY_FOR_BLACKOUT_TIMESERIES_GENERATION: necessity_for_blackout_timeseries_generation
        }
    )
    case_definitions = get_case_definitions(input_excel_file, sheet_case_definitions)
    multicriteria_data = get_multicriteria_data(
        input_excel_file, sheet_multicriteria_data, case_definitions
    )

    return (
        settings,
        parameters_constant_values,
        parameters_sensitivity,
        project_site_s,
        case_definitions,
        multicriteria_data,
    )


def get_data(file, sheet, header_row, index_column, last_column):
    # Gets data from excel template
    if index_column == None and last_column == None:
        data = pd.read_excel(file, sheet_name=sheet, header=header_row - 1, index_col=0)
        data = data.dropna(axis=1)
    else:
        data = pd.read_excel(
            file,
            sheet_name=sheet,
            header=header_row - 1,
            index_col=0,
            usecols=index_column + ":" + last_column,
        )
        data = data.dropna()
    return data


def identify_true_false(entry):
    # Translates strings True/False to boolean
    if entry == "True":
        entry = True
    elif entry == "False":
        entry = False
    else:
        pass

    return entry


def get_settings(file, sheet_settings):
    # defines dictionary connected to settings
    settings = get_data(file, sheet_settings, 11, "B", "C")
    settings = settings.to_dict(orient="dict")
    settings = settings[SETTING_VALUE]

    # Translate strings 'True' and 'False' from excel sheet to True and False
    for key in settings:
        settings[key] = identify_true_false(settings[key])
    return settings


def get_parameters_constant(file, sheet_input_constant):
    # defines dictionary connected to parameters
    parameters_constant = get_data(file, sheet_input_constant, 6, "A", "C")
    parameters_constant = parameters_constant.to_dict(orient="dict")
    parameters_constant_units = parameters_constant[UNIT]
    parameters_constant_values = parameters_constant[VALUE]

    if FUEL_CO2_EMISSION_FACTOR not in parameters_constant_values.keys():
        parameters_constant_values.update({FUEL_CO2_EMISSION_FACTOR: 2.68})
        parameters_constant_units.update({FUEL_CO2_EMISSION_FACTOR: "kgCO2/l"})
        logging.warning(
            "Optional parameter `fuel_co2_emission_factor` was not included in the input parameters."
            "The CO2 emissions will be calculated with the default value of 2.68 kgCO2/l diesel"
        )

    if MAINGRID_CO2_EMISSION_FACTOR not in parameters_constant_values.keys():
        parameters_constant_values.update({MAINGRID_CO2_EMISSION_FACTOR: 0.9})
        parameters_constant_units.update({MAINGRID_CO2_EMISSION_FACTOR: "kgCO2/kWh"})
        logging.warning(
            "Optional parameter `maingrid_co2_emission_factor` was not included in the input parameters."
            "The CO2 emissions will be calculated with the default value of 0.9 kgCO2/ kWh "
            "consumed from the (fully coal-based) maingrid."
        )

    # print(parameters_constant_values)
    return parameters_constant_units, parameters_constant_values


def get_parameters_sensitivity(file, sheet_input_sensitivity):
    # defines dictionary connected to senstivity analysis
    parameters_sensitivity = get_data(file, sheet_input_sensitivity, 10, "A", "D")
    parameters_sensitivity = parameters_sensitivity.to_dict(orient="index")
    return parameters_sensitivity


def get_project_sites(file, sheet_project_sites):
    # defines dictionary connected to project sites
    project_sites = get_data(file, sheet_project_sites, 14, None, None)
    project_sites = project_sites.to_dict(orient="index")

    # Print all evaluated locations in terminal
    project_site_name_string = ""
    for project_site_name in project_sites.keys():
        project_site_name_string += project_site_name + ", "
    logging.info(
        "Following project locations are evaluated: " + project_site_name_string[:-2]
    )

    # Translate strings 'True' and 'False' from excel sheet to True and False
    for site in project_sites:
        for key in project_sites[site]:
            project_sites[site][key] = identify_true_false(project_sites[site][key])
    return project_sites


def get_case_definitions(file, sheet_project_sites):
    # defines dictionary connected to project sites
    case_definitions = get_data(file, sheet_project_sites, 17, None, None)
    # if any(case_definitions.columns.str.contains('unnamed', case=False)):
    #    logging.warning('Input template: Tab CASE_DEFINITIONS might have unnamed columns, which will be dropped. Check if all your cases are simulated.')
    #    case_definitions.drop(case_definitions.columns[case_definitions.columns.str.contains('unnamed', case=False)], axis=1, inplace=True)

    case_definitions = case_definitions.to_dict(orient="dict")

    # Translate strings 'True' and 'False' from excel sheet to True and False

    for case in case_definitions:
        case_definitions[case].update({CASE_NAME: case})
        for key in case_definitions[case]:
            case_definitions[case][key] = identify_true_false(
                case_definitions[case][key]
            )
        if case_definitions[case][MAX_SHORTAGE] != DEFAULT:
            case_definitions[case].update(
                {MAX_SHORTAGE: float(case_definitions[case][MAX_SHORTAGE])}
            )

        if case_definitions[case][EVALUATION_PERSPECTIVE] not in [
            AC_SYSTEM,
            DC_SYSTEM,
        ]:
            logging.error(
                "Parameter evaluation_perspective has to be either 'AC_system' or 'DC_system', "
                "but is ",
                case_definitions[case][EVALUATION_PERSPECTIVE],
            )

        case_definitions[case].update(
            {
                NUMBER_OF_EQUAL_GENERATORS: int(
                    case_definitions[case][NUMBER_OF_EQUAL_GENERATORS]
                )
            }
        )
    return case_definitions


def get_multicriteria_data(file, sheet_multicriteria_analysis, case_definitions):
    # gets weights of the dimensions
    dimension_weights = pd.read_excel(
        file,
        sheet_name=sheet_multicriteria_analysis,
        header=10 - 1,
        nrows=4,
        usecols="A:B",
    )
    dimension_weights = dimension_weights.to_dict(orient="index")

    # gets weights of the criteria
    criteria_weights = pd.read_excel(
        file,
        sheet_name=sheet_multicriteria_analysis,
        header=17 - 1,
        nrows=12,
        usecols="B:I",
    )
    criteria_weights = criteria_weights.to_dict(orient="index")

    # gets whether a parameter of the sensibility analysis must be considered in the multicriteria analysis or not
    parameters = pd.read_excel(
        file,
        sheet_name=sheet_multicriteria_analysis,
        header=33 - 1,
        nrows=18,
        usecols="A:B",
    )
    parameters = parameters.to_dict(orient="index")

    multicriteria_data = {
        DIMENSIONS: dimension_weights,
        CRITERIA: criteria_weights,
        PARAMETERS: parameters,
    }

    # gets the tariff for each case scenario from the case_definitions dictionary
    multicriteria_data[TARIFF] = {}
    for case in case_definitions:
        for key in case_definitions[case]:
            if key == "tariff for electrical service":
                tariff = case_definitions[case][key]
                if tariff != "None":
                    multicriteria_data[TARIFF][case] = float(tariff)
                else:
                    multicriteria_data[TARIFF][case] = tariff

    return multicriteria_data


def column_not_existant(column_item, column_title, path_from):
    logging.error(
        'A column with the header "'
        + column_title
        + '" as defined in the excel input file, tab "project sites", with "'
        + column_item
        + '" could not be found in '
        + "\n        "
        + path_from
        + "\n        Check whether column exists, spelling is correct and for correct seperator of .csv file."
    )
    sys.exit(1)  # Shutting down programm


def from_file(project_site, path_from):
    ##########################################################
    # Reads timeseries from files connected to project sites #
    ##########################################################
    data_set = pd.read_csv(path_from, sep=project_site[SEPARATOR])

    list_columns = [
        TITLE_TIME,
        TITLE_DEMAND_AC,
        TITLE_DEMAND_DC,
        TITLE_PV,
        TITLE_WIND,
        TITLE_GRID_AVAILABILITY,
    ]

    # Attached data to each project site analysed. Does NOT apply noise here,
    # as noise might be subject to sensitivity analysis

    # Necessary: All of these input timeseries in same unit (kWh)

    # If-else clauses allow that some of the timeseries are not included in csv file.

    for column_item in list_columns:
        if column_item == TITLE_TIME:
            if project_site[column_item] == "None":
                file_index = None
            else:
                try:
                    file_index = pd.DatetimeIndex(
                        data_set[project_site[TITLE_TIME]].values
                    )
                except (KeyError):
                    column_not_existant(
                        column_item, project_site[column_item], path_from
                    )
            project_site.update({FILE_INDEX: file_index})

        else:
            if column_item == TITLE_DEMAND_AC:
                dictionary_title = DEMAND_AC
            elif column_item == TITLE_DEMAND_DC:
                dictionary_title = DEMAND_DC
            elif column_item == TITLE_PV:
                dictionary_title = PV_GENERATION_PER_KWP
            elif column_item == TITLE_WIND:
                dictionary_title = WIND_GENERATION_PER_KW
            elif column_item == TITLE_GRID_AVAILABILITY:
                dictionary_title = GRID_AVAILABILITY

            if project_site[column_item] != "None":
                try:
                    project_site.update(
                        {dictionary_title: data_set[project_site[column_item]]}
                    )
                except (KeyError):
                    column_not_existant(
                        column_item, project_site[column_item], path_from
                    )
            else:
                if column_item != TITLE_GRID_AVAILABILITY:
                    if project_site[column_item] != "None":
                        logging.warning(
                            "It is assumed that timeseries "
                            + column_item[6:]
                            + " is a vector of zeroes."
                        )
                    project_site.update(
                        {dictionary_title: pd.Series([0 for i in range(0, 8760)])}
                    )

    return


def check_output_directory(settings, input_excel_file):

    logging.debug("Checking for folders and files")
    """ Checking for output folder, creating it if nonexistant and deleting files if needed """
    import os
    import shutil

    output_folder = settings[OUTPUT_FOLDER]
    folder_list = [
        LP_FILES_FOLDER,
        STORAGE_FOLDER,
        ELECTRICITY_MG_FOLDER,
        INPUTS_FOLDER,
        OEMOF_FOLDER,
    ]

    if os.path.isdir(output_folder) == True:
        # Empty folders with previous result, except oemof results if simulation restart
        for folder in folder_list:
            # Delete all folders. Special case: oemof folder
            if folder == OEMOF_FOLDER and os.path.isdir(output_folder + folder) == True:
                # dont delete oemof folder if necessary for restoring results
                if settings[RESTORE_OEMOF_IF_EXISTENT] == True:
                    pass
                # delete oemof folder if no restoring necessary
                else:
                    path_removed = os.path.abspath(output_folder + folder)
                    shutil.rmtree(path_removed, ignore_errors=True)
                    os.mkdir(output_folder + OEMOF_FOLDER)

            elif (
                folder == OEMOF_FOLDER
                and os.path.isdir(output_folder + folder) == False
            ):
                os.mkdir(output_folder + OEMOF_FOLDER)

            elif os.path.isdir(output_folder + folder):
                path_removed = os.path.abspath(output_folder + folder)
                shutil.rmtree(path_removed, ignore_errors=True)

        # remove other results in output folder (log, csv)
        for root, dirs, files in os.walk(output_folder):
            for file in files:
                if (
                    file == GRID_AVAILABILITY_CSV
                    and settings[RESTORE_BLACKOUTS_IF_EXISTENT] == False
                ):
                    os.remove(root + "/" + file)
                else:
                    pass
    else:
        os.mkdir(output_folder)
        os.mkdir(output_folder + OEMOF_FOLDER)

    os.mkdir(output_folder + INPUTS_FOLDER)

    path_from = os.path.abspath(input_excel_file)
    path_to = os.path.abspath(os.path.join(output_folder,INPUT_TEMPLATE_EXCEL_XLSX))
    shutil.copy(path_from, path_to)

    if settings[SAVE_LP_FILE] == True or settings[LP_FILE_FOR_ONLY_3_TIMESTEPS] == True:
        os.mkdir(output_folder + LP_FILES_FOLDER)

    if (
        settings[SAVE_TO_CSV_FLOWS_STORAGE] == True
        or settings[SAVE_TO_PNG_FLOWS_STORAGE] == True
    ):
        os.mkdir(output_folder + STORAGE_FOLDER)

    if (
        settings[SAVE_TO_CSV_FLOWS_ELECTRICITY_MG] == True
        or settings[SAVE_TO_PNG_FLOWS_ELECTRICITY_MG] == True
    ):
        os.mkdir(output_folder + ELECTRICITY_MG_FOLDER)
    return
