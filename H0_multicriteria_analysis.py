'''
1. Agafar resultats de costos i capacitats

'''


import logging
import xlsxwriter
import os


weights_dimensions = {'economic': 0.2, 'technical': 0.2, 'social': 0.2, 'environmental': 0.2, 'institutional': 0.2}
weights_criteria = {'EC1': 0.5, 'EC2': 0.5, 'T1': 1 / 3, 'T2': 1 / 3, 'T3': 1 / 3, 'S1': 0.5, 'S2': 0.5,
                        'EN1': 1 / 3, 'EN2': 1 / 3, 'EN3': 1 / 3, 'I1': 1}


class Multicriteria():

    def main_analysis(all_results,project_locations,shortage_levels,settings):
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
        reliable_capacities_projects = []
        nonreliable_capacities_projects = []

        for project_site in all_results:
            project_evaluations = {}
            cases = {'reliable':[],'nonreliable':[]}
            reliable_capacities = {'capacity_pv_kWp':[],'capacity_wind_kW':[],
                                   'capacity_storage_kWh':[],'capacity_genset_kW':[],'capacity_pcoupling_kW':[]}
            nonreliable_capacities = {'capacity_pv_kWp': [], 'capacity_wind_kW': [],
                                   'capacity_storage_kWh': [], 'capacity_genset_kW': [], 'capacity_pcoupling_kW': []}

            for key in all_results[project_site]:

                case = all_results[project_site][key]


                case_evaluations = {}

                # economic evaluation
                if case['total_demand_supplied_annual_kWh'] == 0: # THIS CASE WILL NOT EXISTS, DELETE WITH FINAL CODE
                    EC1 = 100
                    EC2 = 100
                else:
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
                # distinguis reliable and nonreliable case name
                if T3 < (1-shortage_levels[len(shortage_levels)-1]-0.1):
                    if case['case'] not in cases['nonreliable']:
                        cases['nonreliable'].append(case['case'])
                        for capacity in nonreliable_capacities:
                            nonreliable_capacities[capacity].append(case[capacity])
                else:
                    if case['case'] not in cases['reliable']:
                        cases['reliable'].append(case['case'])
                    for capacity in reliable_capacities:
                        reliable_capacities[capacity].append(case[capacity])

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

            reliable_capacities_projects.append(reliable_capacities)
            nonreliable_capacities_projects.append(nonreliable_capacities)
            evaluations[number] = project_evaluations

            number += 1

        # data is disposed for proceeding to rank the alternatives through compromise programming method
        Compromise.ranking_method(evaluations,project_locations,shortage_levels,cases,
                                  reliable_capacities_projects,nonreliable_capacities_projects,settings)

        return


class Compromise():


    def ranking_method(evaluations,project_locations,shortage_levels,cases,
                       reliable_capacities_projects,nonreliable_capacities_projects,settings):

        # Dimensions and criteria weights (have to be adjusted)


        all_global_evaluations = []
        distances_global_L = []
        distances_global_L1 = []
        distances_global_Linf = []
        distances_local_L = []
        distances_local_L1 = []
        distances_local_Linf = []

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


            reliable_evaluations,nonreliable_evaluations = multicriteria_helpers.distinguish_reliability(global_evaluations,
                                                                                                         shortage_levels)
            all_global_evaluations.append([nonreliable_evaluations, reliable_evaluations])

            L1,Linf,L = Compromise.global_ranking(reliable_evaluations,nonreliable_evaluations)
            distances_global_L1.append(L1)
            distances_global_Linf.append(Linf)
            distances_global_L.append(L)


            L1, Linf, L = Compromise.shortage_ranking(reliable_evaluations,cases,shortage_levels)
            distances_local_L1.append(L1)
            distances_local_Linf.append(Linf)
            distances_local_L.append(L)

            number_project += 1

        multicriteria_helpers.matrix_results_evaluation(all_global_evaluations, project_locations,
                                                        shortage_levels,cases,
                                                        distances_global_L, distances_global_L1, distances_global_Linf,
                                                        distances_local_L, distances_local_L1, distances_local_Linf,
                                                        reliable_capacities_projects,nonreliable_capacities_projects,settings)

        return



    def global_ranking(reliable_evaluations,nonreliable_evaluations):

        if nonreliable_evaluations != {}:
            nonreliable = len(nonreliable_evaluations['economic']['EC1'])
        else:
            nonreliable = 0

        if nonreliable > 0:
            global_evaluations = multicriteria_helpers.create_diccionary([])
            for dimension in global_evaluations:
                for criterion in global_evaluations[dimension]:
                    for value in nonreliable_evaluations[dimension][criterion]:
                        global_evaluations[dimension][criterion].append(value)
                    for value in reliable_evaluations[dimension][criterion]:
                        global_evaluations[dimension][criterion].append(value)

            L1, Linf, L = Compromise.rank(global_evaluations)

            L1_reliable = []
            Linf_reliable = []
            L_reliable = []
            L1_nonreliable = []
            Linf_nonreliable = []
            L_nonreliable = []

            position = 0
            while position < len(L):
                if position < nonreliable:
                    L1_nonreliable.append(L1[position])
                    Linf_nonreliable.append(Linf[position])
                    L_nonreliable.append(L[position])
                else:
                    L1_reliable.append(L1[position])
                    Linf_reliable.append(Linf[position])
                    L_reliable.append(L[position])

                position += 1

            return [L1_nonreliable,L1_reliable],[Linf_nonreliable,Linf_reliable],[L_nonreliable,L_reliable]


        else:
            L1, Linf, L = Compromise.rank(reliable_evaluations)
            return [[],L1],[[],Linf],[[],L]


    def shortage_ranking(reliable_evaluations,cases,shortage_levels):

        shortage_L1 = {}
        shortage_Linf = {}
        shortage_L = {}
        reliable_cases = len(cases['reliable'])
        start = 0
        for shortage_level in shortage_levels:
            shortage_evaluations = multicriteria_helpers.create_diccionary([])
            for dimension in reliable_evaluations:
                for criterion in reliable_evaluations[dimension]:
                    i = start
                    values = reliable_evaluations[dimension][criterion]
                    for j in range(reliable_cases):
                        shortage_evaluations[dimension][criterion].append(values[i])
                        i += 1

            L1, Linf, L = Compromise.rank(shortage_evaluations)
            shortage_L1[shortage_level] = L1
            shortage_Linf[shortage_level] = Linf
            shortage_L[shortage_level] = L

            start += reliable_cases

        return shortage_L1,shortage_Linf,shortage_L


    def rank(evaluations):

        ideal_values = {}
        antiideal_values = {}
        for dimension in evaluations:
            for criteria in evaluations[dimension]:
                values = evaluations[dimension][criteria]
                if criteria in ['EC1', 'EC2', 'S1', 'EN1', 'EN2', 'EN3']:
                    ideal_values[criteria] = min(values)
                    antiideal_values[criteria] = max(values)
                else:
                    ideal_values[criteria] = max(values)
                    antiideal_values[criteria] = min(values)

        normalized_evaluations = multicriteria_helpers.create_diccionary([])
        for dimension in evaluations:
            for criteria in evaluations[dimension]:
                values = evaluations[dimension][criteria]
                for value in values:
                    if ideal_values[criteria] == antiideal_values[criteria]:
                        normalized_evaluations[dimension][criteria].append(1) # NEED TO BE CHANGED APPROPIATELY
                    else:
                        normalized_evaluations[dimension][criteria].append(abs(value - ideal_values[criteria]) /
                                                                       abs(ideal_values[criteria] - antiideal_values[
                                                                           criteria]))

        ponderations = {'economic': [], 'technical': [], 'social': [], 'environmental': [], 'institutional': []}
        for dimension in normalized_evaluations:
            first = True
            ponderations_criterion = []
            for criteria in normalized_evaluations[dimension]:
                values = normalized_evaluations[dimension][criteria]
                if first:
                    for value in values:
                        ponderations_criterion.append(weights_criteria[criteria] * value)
                    first = False

                else:
                    for i in range(len(values)):
                        ponderations_criterion[i] = ponderations_criterion[i] + weights_criteria[criteria] * values[i]

            ponderations[dimension] = ponderations_criterion

        L1 = []
        Linf = []
        first = True
        for dimension in ponderations:
            values = ponderations[dimension]
            if first:
                for value in values:
                    L1.append(weights_dimensions[dimension] * value)
                    Linf.append(weights_dimensions[dimension] * value)
                first = False
            else:
                for i in range(len(values)):
                    L1[i] = L1[i] + weights_dimensions[dimension] * values[i]
                    if weights_dimensions[dimension] * values[i] > Linf[i]:
                        Linf[i] = weights_dimensions[dimension] * values[i]

        L = []
        for i in range(len(L1)):
            L.append((L1[i] + Linf[i]) / 2)

        return L1,Linf,L

class Evaluate():
    def linear_evaluation(punctuations,components,case):
        Num = 0
        Den = 0
        for component in punctuations:
            Num += punctuations[component] * case[components[component]]
            Den += case[components[component]]

        if Den == 0:
            return 100
        else:
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
        if number_linear + number_constant > 0:
            return (linear * number_linear + constant * number_constant) / (number_linear + number_constant)
        else:
            return 100 # NEED TO BE CHANGED APPROPIATELY


class multicriteria_helpers():
    def create_diccionary(self):
        economic_eval = {'EC1': [], 'EC2': []}
        technical_eval = {'T1': [], 'T2': [], 'T3': []}
        social_eval = {'S1': [], 'S2': []}
        environmental_eval = {'EN1': [], 'EN2': [], 'EN3': []}
        institutional_eval = {'I1': []}

        return {'economic':economic_eval,'technical':technical_eval,'social':social_eval,
                                  'environmental':environmental_eval,'institutional':institutional_eval}


    def matrix_results_evaluation(all_global_evaluations,project_locations,shortage_levels,cases,
                                  g_Ls,g_L1s,g_Linfs,l_Ls,l_L1s,l_Linfs,
                                  reliable_capacities_projects,nonreliable_capacities_projects,settings):


        columns = {0: 'A', 1: 'B', 2: 'C', 3: 'D', 4: 'E', 5: 'F', 6: 'G', 7: 'H', 8: 'I', 9: 'J'
            , 10: 'K', 11: 'L', 12: 'M', 13: 'N', 14: 'O', 15: 'P', 16: 'Q', 17: 'R', 18: 'S', 19: 'T'
            , 20: 'U', 21: 'V', 22: 'W', 23: 'X', 24: 'Y', 25: 'Z'}


        #if not (os.path.isdir('./MCDA_evaluation_results')):
        #    os.mkdir('./MCDA_evaluation_results')


        workbook = xlsxwriter.Workbook(settings['output_folder']+'/MCDA_evaluation_results.xlsx')

        for i in range(len(all_global_evaluations)):
            reliable_capacities = reliable_capacities_projects[i]
            nonreliable_capacities = nonreliable_capacities_projects[i]
            nonreliable_evaluations = all_global_evaluations[i][0]
            reliable_evaluations = all_global_evaluations[i][1] # ara el primer valor d'això serà nonreliable i el segon reliable
            project = project_locations[i]
            nonreliable_L1 = g_L1s[i][0]
            nonreliable_Linf = g_Linfs[i][0]
            nonreliable_L = g_Ls[i][0]
            reliable_L1 = g_L1s[i][1]
            reliable_Linf = g_Linfs[i][1]
            reliable_L = g_Ls[i][1]

            local_L1 = l_L1s[i]
            local_Linf = l_Linfs[i]
            local_L = l_Ls[i]


            worksheet = workbook.add_worksheet(project)

            format = workbook.add_format({
                'bold': 1,
                'border': 1,
                'align': 'center',
                'valign': 'vcenter'})

            format1 = workbook.add_format({
                'bold': 1,
                'border': 1,
                'fg_color': "#DADCDF",
                'align': 'center',
                'valign': 'vcenter'})

            normal_format = workbook.add_format({
                'border': 1,
                'align': 'center',
                'valign': 'vcenter'})

            normal_format1 = workbook.add_format({
                'border': 1,
                'fg_color': "#DADCDF",
                'align': 'center',
                'valign': 'vcenter'})

            title = workbook.add_format({
                'bold': 1,
                'border': 1,
                'fg_color': "#B8D3FF",
                'align': 'center',
                'valign': 'vcenter'})


            row, col = 0,3
            for i in range (len(cases['nonreliable'])):
                col += 1
            if len(cases['nonreliable']) > 0:
                col += 1

            worksheet.write(row, col, 'Shortage levels', format)
            col += 1
            for i in range(len(shortage_levels)):
                if i % 2 == 0:
                    worksheet.merge_range(str(columns[col]) + '1:' + str(columns[col + len(cases['reliable']) - 1]) + '1',
                                      shortage_levels[i],
                                      format)
                else:
                    worksheet.merge_range(
                        str(columns[col]) + '1:' + str(columns[col + len(cases['reliable']) - 1]) + '1',
                        shortage_levels[i],
                        format1)
                col = col + len(cases['reliable'])

            final = col-1

            row,col = 1,4
            for case in cases['nonreliable']:
                worksheet.write(row, col, case, format1)
                col += 1
            if len(cases['nonreliable']) > 0:
                col += 1
            for i in range(len(shortage_levels)):
                for case in cases['reliable']:
                    if i % 2 == 0:
                        worksheet.write(1, col, case, format)
                    else:
                        worksheet.write(1, col, case, format1)
                    col += 1


            # present main results: capacities of main components
            col = 4
            worksheet.merge_range(str(columns[col]) + '3:' + str(columns[final]) + '3',
                                      'Main results of each optimized scenario',
                                      title)

            row = 3
            for capacity in reliable_capacities:
                worksheet.merge_range('B'+str(row+1)+':D'+str(row+1),
                                      capacity,
                                      format)
                col = 4
                for value in nonreliable_capacities[capacity]:
                    worksheet.write(row, col, value, normal_format1)
                    col += 1
                if len(cases['nonreliable']) > 0:
                    col += 1
                i = 1
                white = True
                for value in reliable_capacities[capacity]:
                    if white:
                        worksheet.write(row, col, value, normal_format)
                    else:
                        worksheet.write(row, col, value, normal_format1)
                    i += 1
                    if i == len(cases['reliable']) + 1:
                        i = 1
                        white = not white
                    col += 1
                row += 1


            # present evaluations
            row,col = 9,0
            worksheet.write(row, col, 'Dimensions', format)
            worksheet.write(row, col+1, 'Weights', format)
            worksheet.write(row, col+2, 'Criteria', format)
            worksheet.write(row, col+3, 'Weights', format)

            col = 4
            worksheet.merge_range(str(columns[col]) + '10:' + str(columns[final]) + '10',
                                  'Evaluations of the criteria',
                                  title)

            worksheet.merge_range('A11:A12', 'Economic', format)
            worksheet.merge_range('B11:B12', weights_dimensions['economic'], format)
            worksheet.merge_range('A13:A15', 'Technical', format)
            worksheet.merge_range('B13:B15', weights_dimensions['technical'], format)
            worksheet.merge_range('A16:A17', 'Social', format)
            worksheet.merge_range('B16:B17', weights_dimensions['social'], format)
            worksheet.merge_range('A18:A20', 'Environmental', format)
            worksheet.merge_range('B18:B20', weights_dimensions['environmental'], format)
            worksheet.write(20, 0, 'Institutional', format)
            worksheet.write(20, 1, weights_dimensions['institutional'], format)
            row, col = 10, 2
            for dimension in reliable_evaluations:
                for criterion in reliable_evaluations[dimension]:
                    worksheet.write(row, col, criterion, format)
                    worksheet.write(row, col+1, weights_criteria[criterion], format)
                    row += 1

            # write evaluations
            row, col = 10, 4
            for dimension in nonreliable_evaluations:
                for criterion in nonreliable_evaluations[dimension]:
                    values = nonreliable_evaluations[dimension][criterion]
                    i = 1
                    for value in values:
                        if i % 2 > 0:
                            worksheet.write(row, col, value, normal_format1)
                        else:
                            worksheet.write(row, col, value, normal_format)
                        i += 1
                        col += 1
                    row += 1
                    col = 4

            row = 10
            if len(cases['nonreliable']) > 0:
                col = 5 + len(cases['nonreliable'])
            else:
                col = 4
            for dimension in reliable_evaluations:
                for criterion in reliable_evaluations[dimension]:
                    values = reliable_evaluations[dimension][criterion]
                    i = 1
                    white = True
                    for value in values:
                        if white:
                            worksheet.write(row, col, value, normal_format)
                        else:
                            worksheet.write(row, col, value, normal_format1)
                        i += 1
                        if i == len(cases['reliable'])+1:
                            i = 1
                            white = not white
                        col += 1
                    row += 1
                    if len(cases['nonreliable']) > 0:
                        col = 5 + len(cases['nonreliable'])
                    else:
                        col = 4

            # results of the compromise programming
            # global
            col = 4
            worksheet.merge_range(str(columns[col]) + '23:' + str(columns[final]) + '23',
                                  'Global ranking',
                                  title)
            row,col = 23,3
            worksheet.write(row, col, 'L1', format)
            for value in nonreliable_L1:
                col += 1
                worksheet.write(row, col, value, normal_format)
            if len(nonreliable_L1) > 0:
                col += 2
            else:
                col = 4
            for value in reliable_L1:
                worksheet.write(row, col, value, normal_format)
                col += 1
            row += 1
            col = 3
            worksheet.write(row, col, 'Linf', format)
            for value in nonreliable_Linf:
                col += 1
                worksheet.write(row, col, value, normal_format)
            if len(nonreliable_Linf) > 0:
                col += 2
            else:
                col = 4
            for value in reliable_Linf:
                worksheet.write(row, col, value, normal_format)
                col += 1
            row += 1
            col = 3
            worksheet.write(row, col, 'L', format)
            for value in nonreliable_L:
                col += 1
                worksheet.write(row, col, value, format)
            if len(nonreliable_L) > 0:
                col += 2
            else:
                col = 4
            for value in reliable_L:
                worksheet.write(row, col, value, format)
                col += 1

            # for each shortage level
            if len(cases['nonreliable']) > 0:
                col = 5 + len(cases['nonreliable'])
            else:
                col = 4
            worksheet.merge_range(str(columns[col]) + '28:' + str(columns[final]) + '28',
                                  'Local ranking for each shortage level',
                                  title)
            row,col = 28,3
            worksheet.write(row, col, 'L1', format)
            if len(cases['nonreliable']) > 0:
                col = 5 + len(cases['nonreliable'])
            else:
                col = 4
            white = True
            for shortage in local_L1:
                for value in local_L1[shortage]:
                    if white:
                        worksheet.write(row, col, value, normal_format)
                    else:
                        worksheet.write(row, col, value, normal_format1)
                    col += 1
                white = not white
            row += 1
            col = 3
            worksheet.write(row, col, 'Linf', format)
            if len(cases['nonreliable']) > 0:
                col = 5 + len(cases['nonreliable'])
            else:
                col = 4
            white = True
            for shortage in local_Linf:
                for value in local_Linf[shortage]:
                    if white:
                        worksheet.write(row, col, value, normal_format)
                    else:
                        worksheet.write(row, col, value, normal_format1)
                    col += 1
                white = not white
            row += 1
            col = 3
            worksheet.write(row, col, 'L', format)
            if len(cases['nonreliable']) > 0:
                col = 5 + len(cases['nonreliable'])
            else:
                col = 4
            white = True
            for shortage in local_L:
                for value in local_L[shortage]:
                    if white:
                        worksheet.write(row, col, value, format)
                    else:
                        worksheet.write(row, col, value, format1)
                    col += 1
                white = not white


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


    def distinguish_reliability(global_evaluations,shortage_levels):

        count = 0
        position = 0
        position_found = False
        i = 0
        while i < len(global_evaluations['technical']['T3']):
            value = global_evaluations['technical']['T3']
            if value[i] < (1-shortage_levels[len(shortage_levels)-1]):
                count += 1
                if not position_found:
                    position = i
                    position_found = True
            i += 1
        nonreliable = count/len(shortage_levels)

        positions_unreliable = []
        n = 1
        while n <= len(shortage_levels):
            positions_unreliable.append((position+1)*n-1)
            n += 1

        if nonreliable == 0: # all cases have acceptable levels of shortage
            reliable_evaluations = global_evaluations
            return reliable_evaluations,{}
        else:
            reliable_evaluations = multicriteria_helpers.create_diccionary([])
            nonreliable_evaluations = multicriteria_helpers.create_diccionary([])
            for dimension in global_evaluations:
                for criterion in global_evaluations[dimension]:
                    values = global_evaluations[dimension][criterion]
                    i = 0
                    while i < len(values):
                        if i not in positions_unreliable:
                            reliable_evaluations[dimension][criterion].append(values[i])
                        elif i == position:
                            nonreliable_evaluations[dimension][criterion].append(values[i])
                        i += 1

            return reliable_evaluations,nonreliable_evaluations


