'''
1. Agafar resultats de costos i capacitats

'''


import logging
import xlsxwriter
import os

class Multicriteria():

    def main_analysis(all_results,project_locations,shortage_levels):
        # keys of dictionary all_results are the filenames, and values are the dictionaries with the results of every case and experiment

        # qualitative indicators
        T2_punctuations = {'pv': 4, 'wind': 0, 'maingrid': 4, 'genset': 2.5}
        #T2_punctuations = {'pv': 4, 'wind': 0, 'maingrid': 4, 'genset': 1.5}

        constant_components = ['maingrid','pv','genset'] # the social evaluation of these components will be constant, the other linear with capacity
        S1_punctuations = {'pv': 2, 'wind': 3, 'genset': 1, 'storage': 2, 'rectifier': 1, 'inverter': 0, 'maingrid': 1}
        # S2 must take into account number of households in population. Just demand? then it will be constant
        S2_punctuations = {'pv': 2, 'wind': 3, 'genset': 1, 'storage': 2, 'rectifier': 1, 'inverter': 0, 'maingrid': 1}


        EN1_punctuations = {'pv': 0, 'wind': 0, 'genset': 0.77, 'maingrid': 0.24} # maingrid factor for Perú
        #EN1_punctuations = {'pv': 0, 'wind': 0, 'genset': 0.85, 'maingrid': 0.24}
        EN2_punctuations = {'pv': 1, 'wind': 3, 'genset': 1, 'storage': 1, 'rectifier': 1, 'inverter': 1, 'maingrid': 0}
        EN3_punctuations = {'pv': 1, 'wind': 1, 'genset': 2, 'storage': 4, 'rectifier': 1, 'inverter': 1, 'maingrid': 0}
        #EN3_punctuations = {'pv': 1, 'wind': 1, 'genset': 3, 'storage': 4, 'rectifier': 1, 'inverter': 1, 'maingrid': 0}
        I1_punctuations = {'pv': 4, 'wind': 3, 'genset': 0, 'maingrid': 3}

        capacities_components = {'pv':'capacity_pv_kWp','wind':'capacity_wind_kW','genset':'capacity_genset_kW','storage':'capacity_storage_kWh',
                 'rectifier':'capacity_rectifier_ac_dc_kW','inverter':'capacity_inverter_dc_ac_kW','maingrid':'capacity_pcoupling_kW'}
        generation_components = {'pv':'total_pv_generation_kWh','wind':'total_wind_generation_kWh',
                                 'genset':'total_genset_generation_kWh','maingrid':'consumption_main_grid_mg_side_annual_kWh'}

        evaluations = {}
        number = 1

        for project_site in all_results:
            project_evaluations = {}
            cases = []

            for key in all_results[project_site]:

                case = all_results[project_site][key]
                if case['case'] not in cases:
                    cases.append(case['case'])

                case_evaluations = {}

                # economic evaluation
                EC1 = case['first_investment']/case['total_demand_supplied_annual_kWh']
                EC2 = case['operation_mantainance_expenditures']/case['total_demand_supplied_annual_kWh']
                economic = {'EC1':EC1,'EC2':EC2}
                case_evaluations['economic'] = economic

                # technical evaluation
                T1 = case['autonomy_factor']
                T2 = Evaluate.linear_evaluation(T2_punctuations, generation_components, case)
                T3 = case['supply_reliability_kWh']
                technical = {'T1':T1,'T2':T2,'T3':T3}
                case_evaluations['technical'] = technical

                # social evaluation
                S1 = Evaluate.mix_evaluation(S1_punctuations,capacities_components,constant_components,case)
                S2 = Evaluate.mix_evaluation(S2_punctuations, capacities_components, constant_components, case)
                social = {'S1':S1,'S2':S2}
                case_evaluations['social'] = social

                # environmental evaluation
                EN1 = Evaluate.linear_evaluation(EN1_punctuations, generation_components, case)
                EN2 = Evaluate.linear_evaluation(EN2_punctuations, capacities_components, case)
                EN3 = Evaluate.linear_evaluation(EN3_punctuations, capacities_components, case)
                environmental = {'EN1':EN1,'EN2':EN2,'EN3':EN3}
                case_evaluations['environmental'] = environmental

                # institutional evaluation
                I1 = Evaluate.linear_evaluation(I1_punctuations, capacities_components, case)
                institutional = {'I1': I1}
                case_evaluations['institutional'] = institutional

                project_evaluations[case['filename']] = case_evaluations


            evaluations[number] = project_evaluations

            number += 1

        # data is disposed for proceeding to rank the alternatives through compromise programming method
        Compromise.ranking_method(evaluations,project_locations,shortage_levels,cases)

        return


class Compromise():
    def ranking_method(evaluations,project_locations,shortage_levels,cases):

        # Dimensions and criteria weights (have to be adjusted)
        weights_dimensions = {'economic':0.2,'technical':0.2,'social':0.2,'environmental':0.2,'institutional':0.2}
        weights_criteria = {'EC1': 0.5,'EC2':0.5,'T1':1/3,'T2':1/3,'T3':1/3,'S1': 0.5,'S2':0.5,
                            'EN1':1/3,'EN2':1/3,'EN3':1/3,'I1':1}

        all_global_evaluations = []
        distances_L = []
        distances_L1 = []
        distances_Linf = []

        number_project = 0
        for project in evaluations:

            economic_eval = {'EC1':[],'EC2':[]}
            technical_eval = {'T1': [], 'T2': [], 'T3': []}
            social_eval = {'S1': [], 'S2': []}
            environmental_eval = {'EN1': [], 'EN2': [], 'EN3': []}
            institutional_eval = {'I1': []}

            for alternative in evaluations[project]:
                case = evaluations[project][alternative]

                economic_eval['EC1'].append(case['economic']['EC1'])
                economic_eval['EC2'].append(case['economic']['EC2'])
                technical_eval['T1'].append(case['technical']['T1'])
                technical_eval['T2'].append(case['technical']['T2'])
                technical_eval['T3'].append(case['technical']['T3'])
                social_eval['S1'].append(case['social']['S1'])
                social_eval['S2'].append(case['social']['S2'])
                environmental_eval['EN1'].append(case['environmental']['EN1'])
                environmental_eval['EN2'].append(case['environmental']['EN2'])
                environmental_eval['EN3'].append(case['environmental']['EN3'])
                institutional_eval['I1'].append(case['institutional']['I1'])

            global_evaluations = {'economic':economic_eval,'technical':technical_eval,'social':social_eval,
                                  'environmental':environmental_eval,'institutional':institutional_eval}


            all_global_evaluations.append(global_evaluations)

            ideal_values = {}
            antiideal_values = {}
            for dimension in global_evaluations:
                for criteria in global_evaluations[dimension]:
                    values = global_evaluations[dimension][criteria]
                    if criteria in ['EC1','EC2','S1','EN1','EN2','EN3']:
                        ideal_values[criteria] = min(values)
                        antiideal_values[criteria] = max(values)
                    else:
                        ideal_values[criteria] = max(values)
                        antiideal_values[criteria] = min(values)


            normalized_evaluations = multicriteria_helpers.create_diccionary([])
            for dimension in global_evaluations:
                for criteria in global_evaluations[dimension]:
                    values = global_evaluations[dimension][criteria]
                    for value in values:
                        normalized_evaluations[dimension][criteria].append(abs(value-ideal_values[criteria])/
                                                                      abs(ideal_values[criteria]-antiideal_values[criteria]))

            ponderations = {'economic': [], 'technical': [], 'social': [], 'environmental': [], 'institutional': []}
            for dimension in normalized_evaluations:
                first = True
                ponderations_criterion = []
                for criteria in normalized_evaluations[dimension]:
                    values = normalized_evaluations[dimension][criteria]
                    if first:
                        for value in values:
                            ponderations_criterion.append(weights_criteria[criteria]*value)
                        first = False

                    else:
                        for i in range(len(values)):
                            ponderations_criterion[i] = ponderations_criterion[i] + weights_criteria[criteria]*values[i]

                ponderations[dimension] = ponderations_criterion

            L1 = []
            Linf = []
            first = True
            for dimension in ponderations:
                values = ponderations[dimension]
                if first:
                    for value in values:
                        L1.append(weights_dimensions[dimension]*value)
                        Linf.append(weights_dimensions[dimension] * value)
                    first = False
                else:
                    for i in range(len(values)):
                        L1[i] = L1[i] + weights_dimensions[dimension] * values[i]
                        if weights_dimensions[dimension] * values[i] > Linf[i]:
                            Linf[i] = weights_dimensions[dimension] * values[i]

            L = []
            for i in range (len(L1)):
                L.append((L1[i]+Linf[i])/2)

            distances_L1.append(L1)
            distances_Linf.append(Linf)
            distances_L.append(L)

            number_project += 1

        multicriteria_helpers.matrix_results_evaluation(all_global_evaluations, project_locations, shortage_levels, cases,
                                          distances_L,distances_L1,distances_Linf)

        return


class Evaluate():
    def linear_evaluation(punctuations,components,case):
        Num = 0
        Den = 0
        for component in punctuations:
            Num += punctuations[component] * case[components[component]]
            Den += case[components[component]]
        return Num / Den

    def constant_evaluation(punctuations, components, case):
        Num = 0
        Den = 0
        for component in punctuations:
            if case[components[component]] > 0:
                Num += punctuations[component]
                Den += 1
        return Num/Den

    def mix_evaluation(punctuations,components,constant_components,case):
        number_linear = 0
        Num_linear = 0
        Den_linear = 0
        for component in punctuations:
            if component not in constant_components and case[components[component]] > 0:
                Num_linear += punctuations[component] * case[components[component]]
                Den_linear += case[components[component]]
                number_linear += 1
        if (Den_linear > 0):
            linear = Num_linear / Den_linear
        else:
            linear = 0
        number_constant = 0
        constant = 0
        for component in punctuations:
            if component in constant_components and case[components[component]] > 0:
                constant += punctuations[component]
                number_constant += 1

        return (linear * number_linear + constant * number_constant) / (number_linear + number_constant)


class multicriteria_helpers():
    def create_diccionary(self):
        economic_eval = {'EC1': [], 'EC2': []}
        technical_eval = {'T1': [], 'T2': [], 'T3': []}
        social_eval = {'S1': [], 'S2': []}
        environmental_eval = {'EN1': [], 'EN2': [], 'EN3': []}
        institutional_eval = {'I1': []}

        return {'economic':economic_eval,'technical':technical_eval,'social':social_eval,
                                  'environmental':environmental_eval,'institutional':institutional_eval}


    def matrix_results_evaluation(all_global_evaluations,project_locations,shortage_levels,cases,Ls,L1s,Linfs):

        columns = {1: 'A', 2: 'B', 3: 'C', 4: 'D', 5: 'E', 6: 'F', 7: 'G', 8: 'H', 9: 'I', 10: 'J'
            , 11: 'K', 12: 'L', 13: 'M', 14: 'N', 15: 'O', 16: 'P', 17: 'Q', 18: 'R', 19: 'S', 20: 'T'
            , 21: 'U', 22: 'V', 23: 'W', 24: 'X', 25: 'Y', 26: 'Z'}

        if not (os.path.isdir('./MCDA_evaluation_results')):
            os.mkdir('./MCDA_evaluation_results')

        workbook = xlsxwriter.Workbook('./MCDA_evaluation_results/Evaluation_results.xlsx')

        for i in range(len(all_global_evaluations)):
            global_evaluations = all_global_evaluations[i]
            project = project_locations[i]
            L1 = L1s[i]
            Linf = Linfs[i]
            L = Ls[i]


            worksheet = workbook.add_worksheet(project)

            merge_format = workbook.add_format({
                'bold': 1,
                'border': 1,
                'align': 'center',
                'valign': 'vcenter'})

            row = 0
            col = 3

            for i in range(len(shortage_levels)):
                worksheet.merge_range(str(columns[col]) + '1:' + str(columns[col + len(cases) -1]) + '1', shortage_levels[i],
                                      merge_format)
                col = col + len(cases)

            worksheet.merge_range('A1:B1', 'shortage levels', merge_format)
            worksheet.write(1, 0, 'Dimension', merge_format)
            worksheet.write(1, 1, 'Criteria', merge_format)
            col = 2
            for shortage in shortage_levels:
                for case in cases:
                    worksheet.write(1, col, case, merge_format)
                    col += 1

            worksheet.merge_range('A3:A4', 'Economic', merge_format)
            worksheet.merge_range('A5:A7', 'Technical', merge_format)
            worksheet.merge_range('A8:A9', 'Social', merge_format)
            worksheet.merge_range('A10:A12', 'Environmental', merge_format)
            worksheet.write(12, 0, 'Institutional', merge_format)

            row, col = 2, 1
            for dimension in global_evaluations:
                for criterion in global_evaluations[dimension]:
                    worksheet.write(row, col, criterion, merge_format)
                    row += 1

            row, col = 2, 2
            for dimension in global_evaluations:
                for criterion in global_evaluations[dimension]:
                    values = global_evaluations[dimension][criterion]
                    for value in values:
                        worksheet.write(row, col, value)
                        col += 1
                    row += 1
                    col = 2

            col = 2
            row += 1
            worksheet.write(row, 1, 'L1', merge_format)
            for element in L1:
                worksheet.write(row, col, element, merge_format)
                col += 1
            col = 2

            row += 1
            worksheet.write(row, 1, 'Linf', merge_format)
            for element in Linf:
                worksheet.write(row, col, element, merge_format)
                col += 1
            col = 2

            row += 1
            worksheet.write(row, 1, 'L', merge_format)
            for element in L:
                worksheet.write(row, col, element, merge_format)
                col += 1

        workbook.close()

        return


    def presentation(all_results,shortage_levels,oemof_results,experiment):

        shortage = experiment['shortage_max_allowed']
        if shortage not in shortage_levels:
            shortage_levels.append(shortage)

        project_site = experiment['project_site_name']
        if project_site in all_results.keys():
            all_results[project_site].update({oemof_results['filename']:oemof_results})
        else:
            all_results.update({project_site:{oemof_results['filename']:oemof_results}})

        return