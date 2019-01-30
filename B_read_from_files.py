import pandas as pd
import logging
# requires xlrd

class csv_input():

    def from_file(project_site):
        ##########################################################
        # Reads timeseries from files connected to project sites #
        ##########################################################

        data_set = pd.read_csv(project_site['timeseries_file'], sep=';')
        if project_site['title_time']=='None':
            file_index = None
        else:
            file_index = pd.DatetimeIndex(data_set[project_site['title_time']].values)

        # Attached data to each project site analysed. Does NOT apply noise here,
        # as noise might be subject to sensitivity analysis

        # Necessary: All of these input timeseries in same unit (kWh)
        project_site.update({'demand': data_set[project_site['title_demand']]})
        project_site.update({'pv_generation_per_kWp': data_set[project_site['title_pv']]})  # reading pv_generation values - adjust to panel area or kWp and if in Wh!
        project_site.update({'wind_generation_per_kW': data_set[project_site['title_wind']]})
        project_site.update({'file_index': file_index})

        return

class excel_template():

    def settings():
        #######################################
        # Reads all input from excel template #
        #######################################

        # location of excel template
        file = './inputs/input_template_excel.xlsx'
        # Name of tabs
        sheet_settings = 'settings'
        sheet_input_constant = 'input_constant'
        sheet_input_sensitivity = 'input_sensitivity'
        sheet_project_sites = 'project_sites'
        sheet_case_definitions = 'case_definitions'

        settings = excel_template.get_settings(file, sheet_settings)
        parameters_constant_units, parameters_constant_values = excel_template.get_parameters_constant(file, sheet_input_constant)
        parameters_sensitivity = excel_template.get_parameters_sensitivity(file, sheet_input_sensitivity)

        project_site_s = excel_template.get_project_sites(file, sheet_project_sites)
        # extend by timeseries
        for project_site in project_site_s:
            csv_input.from_file(project_site_s[project_site])

        case_definitions = excel_template.get_case_definitions(file, sheet_case_definitions)
        return settings, parameters_constant_values, parameters_sensitivity, project_site_s, case_definitions

    def get_data(file, sheet, header_row, index_column, last_column):
        # Gets data from excel template
        if index_column==None and last_column==None:
            data = pd.read_excel(file,
                                 sheet_name=sheet,
                                 header=header_row - 1,
                                 index_col=0)
            data = data.dropna()
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
        parameters_constant = excel_template.get_data(file, sheet_input_constant, 1, "A", "C")
        parameters_constant = parameters_constant.to_dict(orient='dict')
        parameters_constant_units = parameters_constant['Unit']
        parameters_constant_values = parameters_constant['Value']
        return parameters_constant_units, parameters_constant_values

    def get_parameters_sensitivity(file, sheet_input_sensitivity):
        # defines dictionary connected to senstivity analysis
        parameters_sensitivity = excel_template.get_data(file, sheet_input_sensitivity, 1, "A", "D")
        parameters_sensitivity = parameters_sensitivity.to_dict(orient='index')
        return parameters_sensitivity

    def get_project_sites(file, sheet_project_sites):
        # defines dictionary connected to project sites
        project_sites = excel_template.get_data(file, sheet_project_sites, 2, None, None)
        project_site_name_string = ''
        for i in range(0, len(project_sites.columns)):
            project_site_name_string += project_sites.columns[i] + ', '
        logging.info('Following project locations are evaluated: ' + project_site_name_string[:-2])
        project_sites = project_sites.to_dict(orient='index')
        # Translate strings 'True' and 'False' from excel sheet to True and False
        for site in project_sites:
            for key in project_sites[site]:
                project_sites[site][key] = excel_template.identify_true_false(project_sites[site][key])
        return project_sites

    def get_case_definitions(file, sheet_project_sites):
        # defines dictionary connected to project sites
        case_definitions = excel_template.get_data(file, sheet_project_sites, 16, "A", "H")
        # todo: if case_list perform_simulation==False: remove column
        case_definitions = case_definitions.to_dict(orient='dict')
        # Translate strings 'True' and 'False' from excel sheet to True and False
        for case in case_definitions:
            case_definitions[case].update({'case_name': case})
            for key in case_definitions[case]:
                case_definitions[case][key] = excel_template.identify_true_false(case_definitions[case][key])
            if case_definitions[case]['max_shortage'] != 'default':
                case_definitions[case].update({'max_shortage': float(case_definitions[case]['max_shortage'])})
        return case_definitions