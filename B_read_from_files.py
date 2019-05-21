import pandas as pd
import logging
import os
import sys
import shutil
# requires xlrd

class excel_template():

    def settings(input_excel_file):
        #######################################
        # Reads all input from excel template #
        #######################################

        # Name of tabs
        sheet_settings = 'settings'
        sheet_input_constant = 'input_constant'
        sheet_input_sensitivity = 'input_sensitivity'
        sheet_project_sites = 'project_sites'
        sheet_case_definitions = 'case_definitions'

        settings = excel_template.get_settings(input_excel_file, sheet_settings)

        # -------- Check for, create or empty results directory -----------------------#
        from Z_output_functions import output
        output.check_output_directory(settings, input_excel_file)

        parameters_constant_units, parameters_constant_values = excel_template.get_parameters_constant(input_excel_file, sheet_input_constant)
        parameters_sensitivity = excel_template.get_parameters_sensitivity(input_excel_file, sheet_input_sensitivity)

        project_site_s = excel_template.get_project_sites(input_excel_file, sheet_project_sites)

        necessity_for_blackout_timeseries_generation=False
        # extend by timeseries
        for project_site in project_site_s:
            # copy input timeseries to new location
            path_from = os.path.abspath(settings['input_folder_timeseries'] + '/' + project_site_s[project_site]['timeseries_file'])
            path_to = os.path.abspath(settings['output_folder'] + '/inputs/'+ project_site_s[project_site]['timeseries_file'])
            shutil.copy(path_from, path_to)

            csv_input.from_file(project_site_s[project_site], path_from)
            if project_site_s[project_site]['title_grid_availability'] == 'None':
                necessity_for_blackout_timeseries_generation=True

        settings.update({'necessity_for_blackout_timeseries_generation': necessity_for_blackout_timeseries_generation})
        case_definitions = excel_template.get_case_definitions(input_excel_file, sheet_case_definitions)
        return settings, parameters_constant_values, parameters_sensitivity, project_site_s, case_definitions

    def get_data(file, sheet, header_row, index_column, last_column):
        # Gets data from excel template
        if index_column==None and last_column==None:
            data = pd.read_excel(file,
                                 sheet_name=sheet,
                                 header=header_row - 1,
                                 index_col=0)
            data = data.dropna(axis=1)
        else:
            data = pd.read_excel(file,
                                 sheet_name=sheet,
                                 header=header_row-1,
                                 index_col=0,
                                 usecols=index_column+":"+last_column)
            data = data.dropna()
        return data

    def identify_true_false(entry):
        # Translates strings True/False to boolean
        if entry == 'True':
            entry = True
        elif entry == 'False':
            entry = False
        else:
            pass

        return entry

    def get_settings(file, sheet_settings):
        # defines dictionary connected to settings
        settings = excel_template.get_data(file, sheet_settings, 11, "B", "C")
        settings = settings.to_dict(orient='dict')
        settings = settings['setting_value']

        # Translate strings 'True' and 'False' from excel sheet to True and False
        for key in settings:
            settings[key] = excel_template.identify_true_false(settings[key])
        return settings

    def get_parameters_constant(file, sheet_input_constant):
        # defines dictionary connected to parameters
        parameters_constant = excel_template.get_data(file, sheet_input_constant, 6, "A", "C")
        parameters_constant = parameters_constant.to_dict(orient='dict')
        parameters_constant_units = parameters_constant['Unit']
        parameters_constant_values = parameters_constant['Value']
        return parameters_constant_units, parameters_constant_values

    def get_parameters_sensitivity(file, sheet_input_sensitivity):
        # defines dictionary connected to senstivity analysis
        parameters_sensitivity = excel_template.get_data(file, sheet_input_sensitivity, 10, "A", "D")
        parameters_sensitivity = parameters_sensitivity.to_dict(orient='index')
        return parameters_sensitivity

    def get_project_sites(file, sheet_project_sites):
        # defines dictionary connected to project sites
        project_sites = excel_template.get_data(file, sheet_project_sites, 14, None, None)
        project_sites = project_sites.to_dict(orient='index')

        # Print all evaluated locations in terminal
        project_site_name_string = ''
        for project_site_name in project_sites.keys():
            project_site_name_string += project_site_name + ', '
        logging.info('Following project locations are evaluated: ' + project_site_name_string[:-2])

        # Translate strings 'True' and 'False' from excel sheet to True and False
        for site in project_sites:
            for key in project_sites[site]:
                project_sites[site][key] = excel_template.identify_true_false(project_sites[site][key])
        return project_sites

    def get_case_definitions(file, sheet_project_sites):
        # defines dictionary connected to project sites
        case_definitions = excel_template.get_data(file, sheet_project_sites, 16, None, None)
        #if any(case_definitions.columns.str.contains('unnamed', case=False)):
        #    logging.warning('Input template: Tab "case_definitions" might have unnamed columns, which will be dropped. Check if all your cases are simulated.')
        #    case_definitions.drop(case_definitions.columns[case_definitions.columns.str.contains('unnamed', case=False)], axis=1, inplace=True)

        case_definitions = case_definitions.to_dict(orient='dict')
        # Translate strings 'True' and 'False' from excel sheet to True and False

        for case in case_definitions:
            case_definitions[case].update({'case_name': case})
            for key in case_definitions[case]:
                case_definitions[case][key] = excel_template.identify_true_false(case_definitions[case][key])
            if case_definitions[case]['max_shortage'] != 'default':
                case_definitions[case].update({'max_shortage': float(case_definitions[case]['max_shortage'])})

            case_definitions[case].update({'number_of_equal_generators': int(case_definitions[case]['number_of_equal_generators'])})
        return case_definitions

class csv_input():

    def column_not_existant(column_item, column_title, path_from):
        logging.error(
            'A column with the header "'+ column_title + '" as defined in the excel input file, tab "project sites", with "' + column_item + '" could not be found in '
            + '\n        ' + path_from
            + '\n        Check whether column exists, spelling is correct and for correct seperator of .csv file.')
        sys.exit(1) # Shutting down programm

    def from_file(project_site, path_from):
        ##########################################################
        # Reads timeseries from files connected to project sites #
        ##########################################################
        data_set = pd.read_csv(path_from, sep=project_site['seperator'])

        list_columns = ['title_time', 'title_demand_ac', 'title_demand_dc', 'title_pv', 'title_wind', 'title_grid_availability']

        # Attached data to each project site analysed. Does NOT apply noise here,
        # as noise might be subject to sensitivity analysis

        # Necessary: All of these input timeseries in same unit (kWh)

        # If-else clauses allow that some of the timeseries are not included in csv file.

        for column_item in list_columns:
            if column_item == 'title_time':
                if project_site[column_item] == 'None':
                    file_index = None
                else:
                    try:
                        file_index = pd.DatetimeIndex(data_set[project_site['title_time']].values)
                    except (KeyError):
                        csv_input.column_not_existant(column_item, project_site[column_item], path_from)
                project_site.update({'file_index': file_index})

            else:
                if column_item == 'title_demand_ac':
                    dictionary_title = 'demand_ac'
                elif column_item == 'title_demand_dc':
                    dictionary_title = 'demand_dc'
                elif column_item == 'title_pv':
                    dictionary_title = 'pv_generation_per_kWp'
                elif column_item == 'title_wind':
                    dictionary_title = 'wind_generation_per_kW'
                elif column_item == 'title_grid_availability':
                    dictionary_title = 'grid_availability'

                if project_site[column_item] != 'None':
                    try:
                        project_site.update({dictionary_title: data_set[project_site[column_item]]})
                    except (KeyError):
                        csv_input.column_not_existant(column_item, project_site[column_item], path_from)
                else:
                    if column_item != 'title_grid_availability':
                        if project_site[column_item] != 'None':
                            logging.warning('It is assumed that timeseries ' + column_item[6:] + ' is a vector of zeroes.')
                        project_site.update({dictionary_title: pd.Series([0 for i in range(0, 8760)])})

        return
