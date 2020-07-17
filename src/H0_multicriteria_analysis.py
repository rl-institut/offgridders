import logging

import src.H1_multicriteria_functions as multicriteria_functions

def main_analysis(overallresults, multicriteria_data, settings):
    """
    This function rules the multicriteria analysis and calls all other functions
    :param multicriteria_data:
    data for the multicriteria analysis
    :param settings:
    dictionary of settings
    :return:
    """

    all_projects_MCA_data = {
        EVALUATIONS: {},
        NORMALIZED_EVALUATIONS: {},
        "global_Ls": {},
        "local_Ls": {},
    }  # it will store all needed data for the representation of the MCA in excel sheet

    # information from the multicriteria tab in input excel file is set in the right format
    (
        weights_dimensions,
        weights_criteria,
        qualitative_punctuations,
        parameters,
        plot_criteria,
    ) = format_punctuations(multicriteria_data)

    # the cases chosen to analyse in the multicriteria analysis are selected
    (
        all_results,
        cases,
        projects_name,
        sensibility,
    ) = presentation(overallresults, parameters)

    # the multicriteria analysis with sensibility parameters can only be realised if all combinations have been calculated
    if settings[SENSITIVITY_ALL_COMBINATIONS] or not sensibility:
        # criteria are evaluated for all cases
        evaluations, capacities = multicriteria_functions.evaluate_criteria(
            all_results, qualitative_punctuations, multicriteria_data
        )
        all_projects_MCA_data[CAPACITIES] = capacities

        for project in evaluations:
            # all evaluations for a same criterion are put together, to make easier the following ranking
            global_evaluations = prepare_global_evaluations(
                evaluations[project]
            )
            all_projects_MCA_data[EVALUATIONS][project] = global_evaluations

            # first, a global ranking, for all solutions, is calculated
            # evaluations are normalized
            global_normalized_evaluations = multicriteria_functions.normalize_evaluations(
                global_evaluations, weights_criteria, "global"
            )
            all_projects_MCA_data[NORMALIZED_EVALUATIONS][
                project
            ] = global_normalized_evaluations

            # the ranking is calculated
            global_Ls = multicriteria_functions.rank(
                global_normalized_evaluations, weights_dimensions, weights_criteria
            )
            all_projects_MCA_data["global_Ls"][project] = global_Ls

            # then, a local ranking, for each combinations of parameters (if asked), is calculated
            if sensibility:
                # first, the global_evaluations dictionary is splitted in several local_evaluations for each combination of parameters
                local_evaluations = multicriteria_functions.prepare_local_evaluations(
                    global_evaluations, cases
                )

                # second, each local_evaluations are normalized and a ranking is calculated
                local_Ls = []
                for evaluation in local_evaluations:
                    local_normalized_evaluation = multicriteria_functions.normalize_evaluations(
                        evaluation, weights_criteria, "local"
                    )
                    local_Ls_each = multicriteria_functions.rank(
                        local_normalized_evaluation,
                        weights_dimensions,
                        weights_criteria,
                    )
                    local_Ls.append(local_Ls_each)
                all_projects_MCA_data["local_Ls"][project] = local_Ls

        # present results of the multicriteria analysis in excel file
        multicriteria_functions.representation(
            all_projects_MCA_data,
            weights_dimensions,
            weights_criteria,
            cases,
            parameters,
            projects_name,
            settings,
            sensibility,
        )

        # plot criteria evaluations
        multicriteria_functions.plot_evaluations(
            all_projects_MCA_data[EVALUATIONS],
            plot_criteria,
            parameters,
            cases,
            projects_name,
            settings,
        )

    else:
        logging.error(
            "If sensibility parameters must be considered in the multicriteria analysis, "
            "all sensibility combinations must be True in the settings tab of the input excel file"
        )

    return

def presentation(overallresults, parameters):
    """
    This function is used to get the results of the experiments where the parameters of the
    sensibility analysis (which are required to be shown) change
    :param parameters:
    dictionary with the information of the parameters of the sensibility analysis
    :return:
    a dictionary with the solved experiments to consider in the multicriteria analysis
    """

    overallresults = overallresults.to_dict("list")

    cases = []
    for case in overallresults[CASE]:
        if case not in cases:
            cases.append(case)

    results = overallresults.copy()
    overallresults = {}
    previous_project = None
    projects_name = []
    for i in range(len(results[PROJECT_SITE_NAME])):
        project = results[PROJECT_SITE_NAME][i]
        if project not in overallresults:
            overallresults[project] = {}
            for element in results:
                overallresults[project][element] = [results[element][i]]
            previous_project = project
            projects_name.append(project)
        else:
            for element in results:
                overallresults[project][element].append(results[element][i])

    # look at which solved experiments the levels of the parameters of the sensibility analysis change
    for parameter in parameters:
        index = 0
        parameters[parameter]["levels"] = []
        parameters[parameter]["previous_level"] = None
        parameters[parameter]["changes"] = []
        for level in overallresults[previous_project][parameter]:
            if level not in parameters[parameter]["levels"]:
                parameters[parameter]["levels"].append(level)
            if level != parameters[parameter]["previous_level"]:
                parameters[parameter]["changes"].append(index)
                parameters[parameter]["previous_level"] = level
            index += 1

    # selects the solved experiments to keep for the multicriteria analysis (where the parameters levels change)
    experiments2analyse = []
    for parameter in parameters:
        if parameters[parameter]["analyse"] == True:
            if len(experiments2analyse) == 0:
                for change in parameters[parameter]["changes"]:
                    experiments2analyse.append(change)
            else:
                provisional_experiments2analyse = experiments2analyse.copy()
                for change in provisional_experiments2analyse:
                    number_included = 0
                    i = 0
                    while (
                        number_included < len(parameters[parameter]["levels"]) - 1
                    ) and i < len(parameters[parameter]["changes"]):
                        subchange = parameters[parameter]["changes"][i]
                        if subchange > change:
                            experiments2analyse.append(subchange)
                            number_included += 1
                        i += 1

    if len(experiments2analyse) == 0:  # means no sensibility analysis is required
        experiments2analyse.append(0)
        sensibility = False
    else:
        sensibility = True
    provisional_experiments2analyse = experiments2analyse.copy()
    for experiment in provisional_experiments2analyse:
        for i in range(len(cases) - 1):
            experiments2analyse.append(experiment + i + 1)
    experiments2analyse.sort()

    all_results = {}
    for project in overallresults:
        all_results[project] = {}
        for experiment in experiments2analyse:
            filename = overallresults[project][FILENAME][experiment]
            all_results[project][filename] = {}
            for element in overallresults[project]:
                all_results[project][filename][element] = overallresults[project][
                    element
                ][experiment]

    return all_results, cases, projects_name, sensibility

def format_punctuations(multicriteria_data):
    """
    gets weights of dimensions and criteria, and the parameters to show from the sensibility analysis.
    This data is taken from the input excel file
    :return:
    the data from the multicriteria tab in correct format
    """

    weights_dimensions = {}
    for dimension in multicriteria_data[DIMENSION]:
        assessment = multicriteria_data[DIMENSION][dimension]
        weights_dimensions[assessment[DIMENSION]] = assessment["weight"]

    weights_criteria = {}
    punctuations = {}
    plot_criteria = []
    for criterion in multicriteria_data[CRITERIA]:
        assessment = multicriteria_data[CRITERIA][criterion]
        weights_criteria[assessment["Abrev"]] = assessment["weight"]
        punctuations[assessment["Abrev"]] = {
            PV: assessment[PV],
            WIND: assessment[WIND],
            GENSET: assessment["diesel"],
            "maingrid": assessment["maingrid"],
        }
        if assessment["plot"] == "Yes":
            plot_criteria.append(assessment["Abrev"])

    parameters = {}
    for parameter in multicriteria_data[PARAMETERS]:
        assessment = multicriteria_data[PARAMETERS][parameter]
        if isinstance(assessment["parameter"], str):
            if assessment["show"] == 1.0:
                parameters[assessment["parameter"]] = {"analyse": True}
            else:
                parameters[assessment["parameter"]] = {"analyse": False}

    return (
        weights_dimensions,
        weights_criteria,
        punctuations,
        parameters,
        plot_criteria,
    )

def prepare_global_evaluations(evaluations):
    """
    Distributed criteria evaluations together.
    A dictionary of: {CASE_NAME:{"economic":{"EC1":value_case_1_EC1,"EC2":value_case_2_EC2},"technical:{...},...},"case_name_2":{...}...}
    is turned into: {"economic"{"EC1":[value_case_1_EC1,value_case_2_EC1,...],"EC2":[...],"technical":[...],...}
    This helps the whole multicriteria process.
    :return:
    a dictionary with the new format
    """
    global_evaluations = multicriteria_functions.create_diccionary([])
    for alternative in evaluations:
        case = evaluations[alternative]
        for dimension in global_evaluations:
            for criterion in global_evaluations[dimension]:
                global_evaluations[dimension][criterion].append(
                    case[dimension][criterion]
                )

    return global_evaluations
