import pandas as pd
import logging
# requires xlrd

class csv_input():


    def from_file(project_site):
        print(project_site['timeseries_file'])
        data_set = pd.read_csv(project_site['timeseries_file'], sep=';')
        if project_site['title_time']=='None':
            file_index = None
        else:
            file_index = pd.DatetimeIndex(data_set[project_site['title_time']].values)

        project_site.update({'demand': data_set[project_site['title_demand']]})
        project_site.update({'pv_generation_per_kWp': data_set[project_site['title_pv']]})  # reading pv_generation values - adjust to panel area or kWp and if in Wh!
        project_site.update({'wind_generation_per_kW': data_set[project_site['title_wind']]})
        project_site.update({'file_index': file_index})
        #logging.info(
        #    'Total annual pv generation at project site (kWh/a/kWp): ' + str(round(pv_generation_per_kWp.sum())))
        '''
        if display_graphs_solar == True:
            helpers.plot_results(pv_generation_per_kWp[date_time_index], "PV generation at project site",
                                 "Date",
                                 "Power kW")
        '''
        return

class excel_template():

    def settings():
        file = './inputs/input_template_excel.xlsx'
        sheet_settings = 'settings'
        sheet_input_constant = 'input_constant'
        sheet_input_sensitivity = 'input_sensitivity'
        sheet_project_sites = 'project_sites'
        sheet_case_definitions = 'case_definitions'

        settings = excel_template.get_settings(file, sheet_settings)
        parameters_constant_units, parameters_constant_values = excel_template.get_parameters_constant(file, sheet_input_constant)
        parameters_sensitivity = excel_template.get_parameters_sensitivity(file, sheet_input_sensitivity)

        project_site_s = excel_template.get_project_sites(file, sheet_project_sites)
        for project_site in project_site_s:
            csv_input.from_file(project_site_s[project_site])

        case_definitions = excel_template.get_case_definitions(file, sheet_case_definitions)
        return settings, parameters_constant_values, parameters_sensitivity, project_site_s, case_definitions

    def get_data(file, sheet, header_row, index_column, last_column):
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
        if entry == 'True':
            entry = True
        elif entry == 'False':
            entry = False
        else:
            pass

        return entry

    def get_settings(file, sheet_settings):
        settings = excel_template.get_data(file, sheet_settings, 11, "B", "C")
        settings = settings.to_dict(orient='dict')
        settings = settings['setting_value']
        # Translate strings 'True' and 'False' from excel sheet to True and False
        for key in settings:
            settings[key] = excel_template.identify_true_false(settings[key])
        return settings

    def get_parameters_constant(file, sheet_input_constant):
        parameters_constant = excel_template.get_data(file, sheet_input_constant, 1, "A", "C")
        parameters_constant = parameters_constant.to_dict(orient='dict')
        parameters_constant_units = parameters_constant['Unit']
        parameters_constant_values = parameters_constant['Value']
        return parameters_constant_units, parameters_constant_values

    def get_parameters_sensitivity(file, sheet_input_sensitivity):
        parameters_sensitivity = excel_template.get_data(file, sheet_input_sensitivity, 1, "A", "D")
        parameters_sensitivity = parameters_sensitivity.to_dict(orient='index')
        return parameters_sensitivity

    def get_project_sites(file, sheet_project_sites):
        project_sites = excel_template.get_data(file, sheet_project_sites, 2, None, None)
        evaluated_locations = len(project_sites.columns)
        # todo logging of evaluated project sites
        project_site_name_list = [project_sites.columns[i] for i in range(0, len(project_sites.columns))]
        project_sites = project_sites.to_dict(orient='index')
        # Translate strings 'True' and 'False' from excel sheet to True and False
        for site in project_sites:
            for key in project_sites[site]:
                project_sites[site][key] = excel_template.identify_true_false(project_sites[site][key])
        return project_sites

    def get_case_definitions(file, sheet_project_sites):
        case_definitions = excel_template.get_data(file, sheet_project_sites, 16, "A", "H")
        # here: if case_list perform_simulation==False: remove column
        case_definitions = case_definitions.to_dict(orient='dict')
        # Translate strings 'True' and 'False' from excel sheet to True and False
        for case in case_definitions:
            case_definitions[case].update({'case_name': case})
            for key in case_definitions[case]:
                case_definitions[case][key] = excel_template.identify_true_false(case_definitions[case][key])
            if case_definitions[case]['max_shortage'] != 'default':
                case_definitions[case].update({'max_shortage': float(case_definitions[case]['max_shortage'])})
        return case_definitions