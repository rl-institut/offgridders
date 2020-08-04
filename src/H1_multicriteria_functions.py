import logging
import xlsxwriter
import scipy.stats as ss
import pandas as pd
import matplotlib.pyplot as plt
import os
import shutil

from src.constants import (
    PV,
    CAPACITY_PV_KWP,
    WIND,
    CAPACITY_WIND_KW,
    GENSET,
    CAPACITY_GENSET_KW,
    STORAGE,
    CAPACITY_STORAGE_KWH,
    MAINGRID,
    TOTAL_PV_GENERATION_KWH,
    CAPACITY_PCOUPLING_KW,
    TOTAL_WIND_GENERATION_KWH,
    CONSUMPTION_MAIN_GRID_MG_SIDE_ANNUAL_KWH,
    TOTAL_GENSET_GENERATION_KWH,
    FIRST_INVESTMENT,
    OPERATION_MAINTAINANCE_EXPENDITURES,
    REVENUE_MAIN_GRID_FEEDIN_ANNUAL,
    ECONOMIC,
    AUTONOMY_FACTOR,
    SUPPLY_RELIABILITY_KWH,
    TECHNICAL,
    TARIFF,
    CASE,
    SOCIOINSTITUTIONAL,
    ENVIRONMENTAL,
    FILENAME,
    OUTPUT_FOLDER,
    EVALUATIONS,
    ANALYSE,
    LEVELS,
    CAPACITIES,
    CRITERIA,
    NORMALIZED_EVALUATIONS,
    GLOBAL_LS,
    LOCAL_LS,
    CASES_AND_EXPERIMENTS,
    EVALUATION,
    DIMENSIONS_W, EC1, EC2, T1, T2, T3, T4, WEIGHTS, L1, LINF,
    ENVIRONMENTAL_W)


def evaluate_criteria(all_results, qualitative_punctuations, multicriteria_data):
    """
    Criteria are evaluated
    :param qualitative_punctuations:
    punctuations on the technology assessment introduced in the input excel file
    :param multicriteria_data:
    rest of the data for the multicriteria analysis. It is used to take the tariff for electrical service (criteria S2)
    :return:
    A dictionary of all evaluations for all projects
    """

    capacities_components = {
        PV: CAPACITY_PV_KWP,
        WIND: CAPACITY_WIND_KW,
        GENSET: CAPACITY_GENSET_KW,
        STORAGE: CAPACITY_STORAGE_KWH,
        MAINGRID: CAPACITY_PCOUPLING_KW,
    }
    generation_components = {
        PV: TOTAL_PV_GENERATION_KWH,
        WIND: TOTAL_WIND_GENERATION_KWH,
        GENSET: TOTAL_GENSET_GENERATION_KWH,
        MAINGRID: CONSUMPTION_MAIN_GRID_MG_SIDE_ANNUAL_KWH,
    }

    evaluations = {}
    capacities = {}
    number = 1

    for project_site in all_results:
        project_evaluations = {}
        project_capacities = {
            CAPACITY_PV_KWP: [],
            CAPACITY_WIND_KW: [],
            CAPACITY_STORAGE_KWH: [],
            CAPACITY_GENSET_KW: [],
            CAPACITY_PCOUPLING_KW: [],
        }

        for cases in all_results[project_site]:

            case = all_results[project_site][cases]
            for capacity in project_capacities:
                project_capacities[capacity].append(case[capacity])

            case_evaluations = {}

            # economic evaluation
            EC1_Result = case[FIRST_INVESTMENT]
            EC2_Result = case[OPERATION_MAINTAINANCE_EXPENDITURES]
            if REVENUE_MAIN_GRID_FEEDIN_ANNUAL in case.keys() and isinstance(
                REVENUE_MAIN_GRID_FEEDIN_ANNUAL, float
            ):
                EC2_Result = EC2_Result - case[REVENUE_MAIN_GRID_FEEDIN_ANNUAL]
            economic = {
                EC1: EC1_Result,
                EC2: EC2_Result,
            }  # Here str are conserved as a variable is prevously declarated with the same name
            case_evaluations[ECONOMIC] = economic

            # technical evaluation
            T1_Result = case[AUTONOMY_FACTOR]
            T2_Result = case[SUPPLY_RELIABILITY_KWH]
            T3_Results = linear_evaluation(
                qualitative_punctuations, generation_components, case, T3
            )
            T4_Results = linear_evaluation(
                qualitative_punctuations, generation_components, case, T4
            )
            technical = {T1: T1_Result, T2: T2_Result, T3: T3_Results, T4: T4_Results}
            case_evaluations[TECHNICAL] = technical

            # socioinstitutional evaluation
            S1 = linear_evaluation(
                qualitative_punctuations, generation_components, case, "S1"
            )
            S2 = multicriteria_data[TARIFF][case[CASE]]
            S3 = linear_evaluation(
                qualitative_punctuations, generation_components, case, "S3"
            )
            socioinstitutional = {"S1": S1, "S2": S2, "S3": S3}
            case_evaluations[SOCIOINSTITUTIONAL] = socioinstitutional

            # environmental evaluation
            EN1 = linear_evaluation(
                qualitative_punctuations, generation_components, case, "EN1"
            )
            EN2 = linear_evaluation(
                qualitative_punctuations, capacities_components, case, "EN2"
            )
            EN3 = linear_evaluation(
                qualitative_punctuations, capacities_components, case, "EN3"
            )
            environmental = {"EN1": EN1, "EN2": EN2, "EN3": EN3}
            case_evaluations[ENVIRONMENTAL] = environmental

            project_evaluations[case[FILENAME]] = case_evaluations

        evaluations[number] = project_evaluations
        capacities[number] = project_capacities

        number += 1

    return evaluations, capacities


def normalize_evaluations(global_evaluations, weights_criteria, type):
    """
    Normalize evaluations
    :param weights_criteria:
    weights of the criteria. If all evaluations for one criterion are the same, the normalization is not possible.
    In this case, all values are turned into "None", the weight of this criterion is converted to 0 and the weights
    of the other criteria from the same dimensions are proportionally increased so the sum keeps equal to 1
    :param type:
    type can either be global (all solutions at once) or local (cases inside each combination of parameters of the sensibility analysis).
    Only when global normalization is carried out, weights of criteria can be changed as said
    :return:
    the normalized evaluations
    """

    # selects the idea value and the anti-ideal value for each criterion (maximum or minimum depending
    # the criterion beneficial or damaging nature)
    ideal_values = {}
    antiideal_values = {}

    for dimension in global_evaluations:
        for criterion in global_evaluations[dimension]:
            values = global_evaluations[dimension][criterion]
            if "None" in values:
                ideal_values[criterion] = "None"
                antiideal_values[criterion] = "None"
            else:
                if criterion in [EC1, EC2, "S2", "EN1"]:
                    ideal_values[criterion] = min(values)
                    antiideal_values[criterion] = max(values)
                else:
                    ideal_values[criterion] = max(values)
                    antiideal_values[criterion] = min(values)

    # build a dictionary with the normalized evaluations
    normalized_evaluations = create_diccionary([])
    for dimension in global_evaluations:
        for criterion in global_evaluations[dimension]:
            values = global_evaluations[dimension][criterion]
            for value in values:
                if ideal_values[criterion] == antiideal_values[criterion]:
                    normalized_evaluations[dimension][criterion].append("None")
                    if type == "global":
                        logging.debug(
                            "All cases are equal for this criterion. Therefore, criterion weight is turned into 0"
                        )
                        change_weights(weights_criteria, dimension, criterion)
                else:
                    normalized_evaluations[dimension][criterion].append(
                        abs(value - ideal_values[criterion])
                        / abs(ideal_values[criterion] - antiideal_values[criterion])
                    )

    return normalized_evaluations


def rank(normalized_evaluations, weights_dimensions, weights_criteria):
    """
    It gets the normalized evaluations and return the distances to the global solutions that will allow to rank the solutions
    :param weights_dimensions:
    weights of the dimensions
    :param weights_criteria:
    weights of the criteria
    :return:
    three distances to the ideal solution. L1 and Linf use metrics 1 and infinite in the formula of the compromise ranking method.
    Then, L is the average value of the other two and will be used to rank the solutions
    """
    # first, the evaluations are pondered
    ponderations = {
        ECONOMIC: [],
        TECHNICAL: [],
        SOCIOINSTITUTIONAL: [],
        ENVIRONMENTAL: [],
    }
    for dimension in normalized_evaluations:
        first = True
        ponderations_criterion = []
        for criteria in normalized_evaluations[dimension]:
            values = normalized_evaluations[dimension][criteria]
            if first:
                for value in values:
                    if value != "None":
                        ponderations_criterion.append(
                            weights_criteria[criteria] * value
                        )
                        first = False

            else:
                for i in range(len(values)):
                    if values[i] != "None":
                        ponderations_criterion[i] = (
                            ponderations_criterion[i]
                            + weights_criteria[criteria] * values[i]
                        )

        ponderations[dimension] = ponderations_criterion

    # then, the three distances are calculated
    L1 = []
    Linf = []
    first = True
    for dimension in ponderations:
        values = ponderations[dimension]
        if first:
            for value in values:
                if value != "None":
                    L1.append(weights_dimensions[dimension] * value)
                    Linf.append(weights_dimensions[dimension] * value)
            first = False
        else:
            for i in range(len(values)):
                if values[i] != "None":
                    L1[i] = L1[i] + weights_dimensions[dimension] * values[i]
                    if weights_dimensions[dimension] * values[i] > Linf[i]:
                        Linf[i] = weights_dimensions[dimension] * values[i]

    L = []
    for i in range(len(L1)):
        L.append((L1[i] + Linf[i]) / 2)

    Ls = [L1, Linf, L]

    return Ls


def prepare_local_evaluations(global_evaluations, cases):
    """
    This functions is used to select only the evaluations of cases inside each combination of parameters of the sensibility analysis,
    to then proceed to normalize these evaluations and rank them
    :param cases:
    the electrification scenarios
    :return:
    a list of dictionaries which contain only the evaluations of electrification cases for each combination of parameters
    """
    local_evaluations = []
    start = 0
    for j in range(int(len(global_evaluations[ECONOMIC][EC1]) / len(cases))):
        local_evaluation = create_diccionary([])
        for dimension in global_evaluations:
            for criterion in global_evaluations[dimension]:
                i = start
                values = global_evaluations[dimension][criterion]
                for j in range(len(cases)):
                    local_evaluation[dimension][criterion].append(values[i])
                    i += 1
        start += len(cases)

        local_evaluations.append(local_evaluation)

    return local_evaluations


def linear_evaluation(qualitative_punctuations, components, case, criterion):
    """
    this function is used to calculate the evaluations for the qualitative criteria, using the capacities
    and electricity generated by the different sources
    :param components:
    dictionary to change names so it can read all_results dictionary
    :param case:
    the information of the solution for this particular electrification case and experiment
    :param criterion:
    the criterion of study
    :return:
    the linear evaluation of this criterion for this case study and experiment
    """
    punctuations = qualitative_punctuations[criterion]
    Num = 0
    Den = 0

    if criterion == "EN3":
        for component in components:
            if component == STORAGE:
                punc = punctuations[PV]
            else:
                punc = punctuations[component]
            if punc == "None":
                punc = 0
            Num += punc * case[components[component]]
            if punc != 0:
                Den += case[components[component]]

    else:
        for component in punctuations:
            punc = punctuations[component]
            if not isinstance(punc, str):
                Num += punc * case[components[component]]
                Den += case[components[component]]

    if Den == 0:
        logging.debug(
            "No component included in this case has capacity over 0: "
            + case[CASE]
            + ". 1 is returned"
        )
        return 1
    else:
        return Num / Den


def create_diccionary(self):
    """
    :return:
    a template of the dictionary for the multicriteria analysis
    """
    economic_eval = {EC1: [], EC2: []}
    technical_eval = {T1: [], T2: [], T3: [], T4: []}
    socioinstitutional_eval = {"S1": [], "S2": [], "S3": []}
    environmental_eval = {"EN1": [], "EN2": [], "EN3": []}

    dictionary = {
        ECONOMIC: economic_eval,
        TECHNICAL: technical_eval,
        SOCIOINSTITUTIONAL: socioinstitutional_eval,
        ENVIRONMENTAL: environmental_eval,
    }

    return dictionary


def change_weights(weights_criteria, dimension, criterion):
    """
    This function changes weights if one criterion sees no differences between solutions
    (minimum value achieved by the criterion equals the maximum)
    :param dimension:
    the dimension of the conflictive criterion
    :param criterion:
    the conflictive criterion
    :return:
    """
    weights_criteria[criterion] = 0
    if dimension == ECONOMIC:
        criteria = [EC1, EC2]
    elif dimension == TECHNICAL:
        criteria = [T1, T2, T3, T4]
    elif dimension == SOCIOINSTITUTIONAL:
        criteria = ["S1", "S2", "S3"]
    elif dimension == ENVIRONMENTAL:
        criteria = ["EN1", "EN2", "EN3"]

    total = 0
    for criterion in criteria:
        total += weights_criteria[criterion]

    if total > 0:
        for criterion in criteria:
            weights_criteria[criterion] = weights_criteria[criterion] / total

    return


def representation(
    all_data,
    weights_dimensions,
    weights_criteria,
    cases,
    parameters,
    projects_name,
    settings,
    sensibility,
):
    """
    This function carries out the representation of the multicriteria analysis in excel sheet
    :param weights_dimensions:
    weights of dimensions
    :param weights_criteria:
    weights of criteria
    :param cases:
    electrification cases
    :param parameters:
    dictionary with the information of the parameters of the sensibility analysis
    :param projects_name:
    list of the project_sites names that are considered in this simulation
    :param settings:
    settings dictinary, to take the output folder
    :param sensibility:
    boolean variable to see if one or more parameters of the sensibility analysis has been considered in this multicriteria analysis.
    True if one or more "TRUE" is written for any parameter in the multicriteria tab in the input excel file
    :return:
    """
    # necessary to convert number to letters in excel
    columns = {
        0: "A",
        1: "B",
        2: "C",
        3: "D",
        4: "E",
        5: "F",
        6: "G",
        7: "H",
        8: "I",
        9: "J",
        10: "K",
        11: "L",
        12: "M",
        13: "N",
        14: "O",
        15: "P",
        16: "Q",
        17: "R",
        18: "S",
        19: "T",
        20: "U",
        21: "V",
        22: "W",
        23: "X",
        24: "Y",
        25: "Z",
        26: "AA",
        27: "AB",
        28: "AC",
        29: "AD",
        30: "AE",
        31: "AF",
        32: "AG",
        33: "AH",
        34: "AI",
        35: "AJ",
        36: "AK",
        37: "AL",
        38: "AM",
        39: "AN",
        40: "AO",
        41: "AP",
        42: "AQ",
        43: "AR",
        44: "AS",
        45: "AT",
        46: "AU",
        47: "AV",
        48: "AW",
        49: "AX",
        50: "AY",
        51: "AZ",
    }

    workbook = xlsxwriter.Workbook(settings[OUTPUT_FOLDER] + "/MCA_evaluations.xlsx")

    for n in range(len(all_data[EVALUATIONS])):
        # there will be a tab for each project
        worksheet = workbook.add_worksheet(projects_name[n])

        # different style options are used
        format_highlight = workbook.add_format(
            {"bold": 1, "border": 1, "align": "center", "valign": "vcenter"}
        )
        format_highlight2 = workbook.add_format(
            {
                "bold": 1,
                "border": 1,
                "fg_color": "#DADCDF",
                "align": "center",
                "valign": "vcenter",
            }
        )
        format_text = workbook.add_format(
            {"border": 1, "align": "center", "valign": "vcenter"}
        )
        format_text2 = workbook.add_format(
            {
                "border": 1,
                "fg_color": "#DADCDF",
                "align": "center",
                "valign": "vcenter",
            }
        )
        format_title = workbook.add_format(
            {
                "bold": 1,
                "border": 1,
                "fg_color": "#B8D3FF",
                "align": "center",
                "valign": "vcenter",
            }
        )

        row, col = 0, 3
        # write parameters and values of the sensibility analysis that are considered for the multicriteria analysis
        parameters_name = []
        for parameter in parameters:
            if parameters[parameter][ANALYSE] == True:
                worksheet.write(row, col, parameter, format_highlight)
                parameters_name.append(parameter)
                row += 1

        row, col, final = 0, 4, 4
        first = True
        for parameter in parameters:
            if parameters[parameter][ANALYSE] == True:
                del parameters_name[0]
                cells = len(cases)
                for param in parameters_name:
                    cells = cells * len(parameters[param][LEVELS])
                if first:
                    for level in parameters[parameter][LEVELS]:
                        worksheet.merge_range(
                            str(columns[col])
                            + str(row + 1)
                            + ":"
                            + str(columns[col + cells - 1])
                            + str(row + 1),
                            level,
                            format_highlight,
                        )
                        col = col + cells
                    final = col
                    row += 1
                    col = 4
                    first = False
                else:
                    while col < final:
                        for level in parameters[parameter][LEVELS]:
                            worksheet.merge_range(
                                str(columns[col])
                                + str(row + 1)
                                + ":"
                                + str(columns[col + cells - 1])
                                + str(row + 1),
                                level,
                                format_highlight,
                            )
                            col = col + cells
                    row += 1
                    col = 4

        if not sensibility:
            final = final + len(cases)

        i, j = 0, 1
        while col < final:
            for case in cases:
                if i % 2 == 0:
                    worksheet.write(row, col, case, format_highlight)
                    worksheet.write(
                        row + 1, col, "case_" + str(j), format_highlight
                    )  # easy name to reference case and experiment when plotting
                    j += 1
                else:
                    worksheet.write(row, col, case, format_highlight2)
                    worksheet.write(row + 1, col, "case_" + str(j), format_highlight2)
                    j += 1
                col += 1
            i += 1

        # write capacities of main components of each solution
        row += 3
        col = 4
        worksheet.merge_range(
            str(columns[col])
            + str(row + 1)
            + ":"
            + str(columns[final - 1])
            + str(row + 1),
            "Main results of each optimized scenario",
            format_title,
        )

        row += 1
        for capacity in all_data[CAPACITIES][n + 1]:
            worksheet.merge_range(
                "B" + str(row + 1) + ":D" + str(row + 1), capacity, format_highlight
            )

            col = 4
            i = 0
            for value in all_data[CAPACITIES][n + 1][capacity]:
                if i / (len(cases) * 2) < 0.5:
                    worksheet.write(row, col, round(value, 2), format_text)
                else:
                    worksheet.write(row, col, round(value, 2), format_text2)
                col += 1
                i += 1
                if i == len(cases) * 2:
                    i = 0

            row += 1

        # write evaluations of criteria
        row += 1
        worksheet.merge_range(
            "A" + str(row + 1) + ":B" + str(row + 1), DIMENSIONS_W, format_highlight
        )
        worksheet.merge_range(
            "C" + str(row + 1) + ":D" + str(row + 1), CRITERIA, format_highlight
        )
        col = 4
        worksheet.merge_range(
            str(columns[col])
            + str(row + 1)
            + ":"
            + str(columns[final - 1])
            + str(row + 1),
            "Criteria evaluations",
            format_title,
        )
        row += 1
        worksheet.merge_range(
            "A" + str(row + 1) + ":B" + str(row + 2), "Economic", format_highlight
        )
        worksheet.merge_range(
            "A" + str(row + 3) + ":B" + str(row + 6), "Technical", format_highlight
        )
        worksheet.merge_range(
            "A" + str(row + 7) + ":B" + str(row + 9),
            "Socio-institutional",
            format_highlight,
        )
        worksheet.merge_range(
            "A" + str(row + 10) + ":B" + str(row + 12),
            ENVIRONMENTAL_W,
            format_highlight,
        )
        for dimension in all_data[EVALUATIONS][n + 1]:
            for criterion in all_data[EVALUATIONS][n + 1][dimension]:
                worksheet.merge_range(
                    "C" + str(row + 1) + ":D" + str(row + 1),
                    criterion,
                    format_highlight,
                )
                col = 4
                i = 0
                values = all_data[EVALUATIONS][n + 1][dimension][criterion]
                for value in values:
                    if i / (len(cases) * 2) < 0.5:
                        worksheet.write(row, col, value, format_text)
                    else:
                        worksheet.write(row, col, value, format_text2)
                    col += 1
                    i += 1
                    if i == len(cases) * 2:
                        i = 0
                row += 1

        # write normalized evaluations of criteria
        row += 1
        col = 0
        worksheet.write(row, col, DIMENSIONS_W, format_highlight)
        worksheet.write(row, col + 1, WEIGHTS, format_highlight)
        worksheet.write(row, col + 2, CRITERIA, format_highlight)
        worksheet.write(row, col + 3, WEIGHTS, format_highlight)
        col = 4
        worksheet.merge_range(
            str(columns[col])
            + str(row + 1)
            + ":"
            + str(columns[final - 1])
            + str(row + 1),
            "Criteria normalized evaluations",
            format_title,
        )
        row += 1
        worksheet.merge_range(
            "A" + str(row + 1) + ":" + "A" + str(row + 2), "EC", format_highlight
        )
        worksheet.merge_range(
            "B" + str(row + 1) + ":" + "B" + str(row + 2),
            weights_dimensions[ECONOMIC],
            format_highlight,
        )
        worksheet.merge_range(
            "A" + str(row + 3) + ":" + "A" + str(row + 6), "T", format_highlight
        )
        worksheet.merge_range(
            "B" + str(row + 3) + ":" + "B" + str(row + 6),
            weights_dimensions[TECHNICAL],
            format_highlight,
        )
        worksheet.merge_range(
            "A" + str(row + 7) + ":" + "A" + str(row + 9), "S", format_highlight
        )
        worksheet.merge_range(
            "B" + str(row + 7) + ":" + "B" + str(row + 9),
            weights_dimensions[SOCIOINSTITUTIONAL],
            format_highlight,
        )
        worksheet.merge_range(
            "A" + str(row + 10) + ":" + "A" + str(row + 12), "EN", format_highlight
        )
        worksheet.merge_range(
            "B" + str(row + 10) + ":" + "B" + str(row + 12),
            weights_dimensions[ENVIRONMENTAL],
            format_highlight,
        )
        for dimension in all_data[NORMALIZED_EVALUATIONS][n + 1]:
            for criterion in all_data[NORMALIZED_EVALUATIONS][n + 1][dimension]:
                worksheet.write(row, 2, criterion, format_highlight)
                worksheet.write(row, 3, weights_criteria[criterion], format_highlight)
                col = 4
                i = 0
                values = all_data[NORMALIZED_EVALUATIONS][n + 1][dimension][criterion]
                for value in values:
                    if i / (len(cases) * 2) < 0.5:
                        worksheet.write(row, col, value, format_text)
                    else:
                        worksheet.write(row, col, value, format_text2)
                    col += 1
                    i += 1
                    if i == len(cases) * 2:
                        i = 0
                row += 1

        # write global results of the multicriteria analysis
        row += 1
        col = 4
        worksheet.merge_range(
            str(columns[col])
            + str(row + 1)
            + ":"
            + str(columns[final - 1])
            + str(row + 1),
            "Global ranking",
            format_title,
        )
        row += 1
        worksheet.write(row, 3, L1, format_highlight)
        worksheet.write(row + 1, 3, LINF, format_highlight)
        worksheet.write(row + 2, 3, "L", format_highlight)
        for j in range(len(all_data[GLOBAL_LS][n + 1])):
            L = all_data[GLOBAL_LS][n + 1][j]
            col = 4
            for value in L:
                worksheet.write(row, col, round(value, 2), format_highlight)
                col += 1
            row += 1
        worksheet.write(row, 3, "Ranking", format_highlight)
        L_ranked = ss.rankdata(L)
        col = 4
        for value in L_ranked:
            worksheet.write(row, col, value, format_highlight)
            col += 1

        row += 2
        col = 3
        explanation = (
            "The best overall solution is the one with lowest distance to the ideal solution (L). "
            "If a solution is the best in all criteria, then it would report a distance 0 to the ideal solution."
        )
        worksheet.merge_range(
            "E" + str(row + 1) + ":" + str(columns[final - 1]) + str(row + 1),
            explanation,
            format_text,
        )

        # write local results of the multicriteria analysis, for each combination of parameters
        if sensibility:
            row += 2
            col = 4
            worksheet.merge_range(
                str(columns[col])
                + str(row + 1)
                + ":"
                + str(columns[final - 1])
                + str(row + 1),
                "Local ranking for each combination of parameters",
                format_title,
            )
            row += 1
            start_row = row
            start_col, i = 4, 0
            worksheet.write(row, 3, L1, format_highlight)
            worksheet.write(row + 1, 3, LINF, format_highlight)
            worksheet.write(row + 2, 3, "L", format_highlight)
            for j in range(len(all_data[LOCAL_LS][n + 1])):
                combinations = all_data[LOCAL_LS][n + 1][j]
                if i % 2 == 0:
                    for L in combinations:
                        col = start_col
                        for case in L:
                            worksheet.write(row, col, round(case, 2), format_highlight)
                            col += 1
                        row += 1
                else:
                    for L in combinations:
                        col = start_col
                        for case in L:
                            worksheet.write(row, col, round(case, 2), format_highlight2)
                            col += 1
                        row += 1
                start_col += len(cases)
                row = start_row
                i += 1

    workbook.close()

    return


def plot_evaluations(
    evaluations, plot_criteria, parameters, cases, projects_name, settings
):
    """
    Evaluations of the criteria are plotted, if asked
    :param plot_criteria:
    list of the names of the criteria to plot
    :param parameters:
    dictionary with the information of the parameters for the sensibility analysis.
    Used to see how many combinations (experiment and cases) have to be displayed
    :param cases:
    list of the cases name
    :param projects_name:
    list of the project_sites names that are considered in this simulation
    :param settings:
    settings dictinary, to take the output folder
    :return:
    """
    combinations = len(cases)
    for parameter in parameters:
        if parameters[parameter][ANALYSE] == True:
            combinations = combinations * len(parameters[parameter][LEVELS])

    cases_exp = []
    for i in range(combinations):
        cases_exp.append("case_" + str(i + 1))

    if os.path.isdir(settings[OUTPUT_FOLDER] + "/mca_plots"):
        shutil.rmtree(settings[OUTPUT_FOLDER] + "/mca_plots", ignore_errors=True)
    if len(plot_criteria) > 0:
        os.mkdir(settings[OUTPUT_FOLDER] + "/mca_plots")

    # a bar chart is created for the evaluations of each required criteria and for each project
    for project in evaluations:
        for dimension in evaluations[project]:
            for criterion in evaluations[project][dimension]:
                if criterion in plot_criteria:
                    evaluations_values = evaluations[project][dimension][criterion]
                    df = pd.DataFrame()
                    df[CASES_AND_EXPERIMENTS] = cases_exp
                    df[EVALUATION] = evaluations_values

                    df.plot.bar(
                        x=CASES_AND_EXPERIMENTS,
                        y=EVALUATION,
                        title="Evaluation of the "
                        + dimension
                        + " criterion, "
                        + criterion
                        + ". Project "
                        + projects_name[project - 1],
                    )

                    plt.savefig(
                        settings[OUTPUT_FOLDER]
                        + "/mca_plots"
                        + "/evaluation_"
                        + criterion
                        + "_"
                        + projects_name[project - 1]
                        + ".png",
                        bbox_inches="tight",
                    )

                    plt.close()
                    plt.clf()
                    plt.cla()

    return
