import pandas as pd

# requires xlrd

class excel_input():

    def settings():
        file = './inputs/input_template_excel.xlsx'
        sheet_settings = 'settings'
        sheet_input_constant = 'input_constant'
        sheet_input_sensitivity = 'input_sensitivity'
        sheet_project_sites = 'project_sites'
        sheet_case_definitions = 'case_definitions'

        settings = excel_input.get_settings(file, sheet_settings)
        parameters_constant_units, parameters_constant_values = excel_input.get_parameters_constant(file, sheet_input_constant)
        parameters_sensitivity = excel_input.get_parameters_sensitivity(file, sheet_input_sensitivity)
        project_sites = excel_input.get_project_sites(file, sheet_project_sites)
        case_definitions = excel_input.get_case_definitions(file, sheet_case_definitions)

        return settings, parameters_constant_values, parameters_sensitivity, project_sites, case_definitions

    def get_data(file, sheet, header_row, index_column, last_column):
        data = pd.read_excel(file,
                          sheet_name=sheet,
                          header=header_row-1,
                          index_col=0,
                          usecols=index_column+":"+last_column)
                          #usecols=[i for i in range(index_column-1,last_column)])

        data = data.dropna()
        return data

    def get_settings(file, sheet_settings):
        settings = excel_input.get_data(file, sheet_settings, 11, "B", "C")
        settings = settings.to_dict(orient='dict')
        settings = settings['setting_value']
        return settings

    def get_parameters_constant(file, sheet_input_constant):
        parameters_constant = excel_input.get_data(file, sheet_input_constant, 1, "A", "C")
        parameters_constant = parameters_constant.to_dict(orient='dict')
        parameters_constant_units = parameters_constant['Unit']
        parameters_constant_values = parameters_constant['Value']
        return parameters_constant_units, parameters_constant_values

    def get_parameters_sensitivity(file, sheet_input_sensitivity):
        parameters_sensitivity = excel_input.get_data(file, sheet_input_sensitivity, 1, "A", "D")
        parameters_sensitivity = parameters_sensitivity.to_dict(orient='index')
        return parameters_sensitivity

    def get_project_sites(file, sheet_project_sites):
        project_sites = excel_input.get_data(file, sheet_project_sites, 2, "A", "D")
        evaluated_locations = len(project_sites.columns)
        project_site_name_list = [project_sites.columns[i] for i in range(0, len(project_sites.columns))]
        project_sites = project_sites.to_dict(orient='index')
        return project_sites

    def get_case_definitions(file, sheet_project_sites):
        case_definitions = excel_input.get_data(file, sheet_project_sites, 16, "A", "H")
        case_list = [case_definitions.columns[i] for i in range(0, len(case_definitions.columns))]
        # here: if case_list perform_simulation==False: remove column
        case_definitions = case_definitions.to_dict(orient='dict')
        return case_definitions