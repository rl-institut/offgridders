import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def add_sum_save(number_of_favoured, name):
    number_of_favoured = number_of_favoured.append(
        pd.DataFrame([number_of_favoured[column].values.sum() for column in number_of_favoured.columns],
                     columns=['sum'], index=number_of_favoured.columns).transpose(), sort=False)
    number_of_favoured.to_csv(folder + "evaluation/" + name + "_" + prefix[:-1] + ".csv")

def compare_solutions(costs, favoured, number_of_favoured, case_name, case_list, comparison_value):
    favoured[case_name] = [0 for entry in costs.index]
    for item in costs.index:
        for specific_case in case_list:
            list = case_list.copy()
            list.remove(specific_case)
            if costs[comparison_value + specific_case][item] \
                    < min([costs[comparison_value + case][item] for case in list]):
                favoured[case_name][item] = specific_case
                number_of_favoured[specific_case][file] = number_of_favoured[specific_case][file] + 1

    return favoured, number_of_favoured

def add_statistics(per_stage, capacities_stage, column_name, file):
    per_stage[column_name + ' average'][file] = capacities_stage[column_name].mean()
    per_stage[column_name + ' min'][file] = capacities_stage[column_name].min()
    per_stage[column_name + ' max'][file] = capacities_stage[column_name].max()
    per_stage[column_name + ' std'][file] = capacities_stage[column_name].std()
    return per_stage

def add_statistics_matrix(matrix):
    matrix = matrix.append(pd.DataFrame([matrix[column].values.sum() for column in matrix.columns], columns=['sum'], index=matrix.columns).transpose(), sort=False)
    matrix = matrix.append(pd.DataFrame([matrix[column].values.mean() for column in matrix.columns], columns=['average'], index=matrix.columns).transpose(), sort=False)
    matrix = matrix.append(pd.DataFrame([matrix[column].values.max() for column in matrix.columns], columns=['max'], index=matrix.columns).transpose(), sort=False)
    matrix = matrix.append(pd.DataFrame([matrix[column].values.min() for column in matrix.columns], columns=['min'], index=matrix.columns).transpose(), sort=False)
    return matrix

def plot_x_y_stages(comparison_list_x, comparison_list_y, stage1, stage2, stage3, no_mgs, number):
    comparison_list = comparison_list_y + comparison_list_x
    plots_1 = pd.DataFrame([stage1[name].values for name in comparison_list], index=comparison_list).transpose()
    plots_2 = pd.DataFrame([stage2[name].values for name in comparison_list], index=comparison_list).transpose()
    plots_3 = pd.DataFrame([stage3[name].values for name in comparison_list], index=comparison_list).transpose()
    plots_no = pd.DataFrame([no_mgs[name].values for name in comparison_list], index=comparison_list).transpose()

    for x_value in comparison_list_x:
        for y_value in comparison_list_y:
            if x_value != y_value:
                number += 1
                fig = plots_no.plot.scatter(x=x_value, y=y_value, color='#cc0000', label='No MGs')
                plots_2.plot.scatter(x=x_value, y=y_value, ax=fig, color='#0033cc', label='Stage 2')
                plots_3.plot.scatter(x=x_value, y=y_value, ax=fig, color='#990099', label='Stage 3')
                plots_1.plot.scatter(x=x_value, y=y_value, ax=fig, color='#66cc33', label='Stage 1')
                fig.legend(loc='center left', bbox_to_anchor=(1, 0.5), frameon=False)
                plt.savefig(folder + "evaluation/" + 'graph_' + prefix + str(number) + '.png', bbox_inches="tight")
                plt.close()

    return number

def plot_matrix(matrix, number, c):
    x = 'Additional branch distance [km]' # 'Distance to national grid [km]'
    y = 'Peak demand [kW]'
    number += 1
    plots = pd.DataFrame([matrix[name].values for name in [x,y,c]], index=[x,y,c]).transpose()
    # Delete all outliners, so that 90% of the values remain
    for column in plots.columns:
        q = plots[column].quantile(0.90)
        plots = plots[plots[column] < q]
    number += 1
    fig = plots.plot.hexbin(x=x, y=y, C=c, colormap='viridis', gridsize=30)
    fig.set(title=c)
    plt.savefig(folder + "evaluation/" + 'graph_' + prefix + str(number) + '.png', bbox_inches="tight")
    plt.close()
    return number

def get_crf (grid_arrival):
    crf = (0.16 * (1+ 0.16) ** grid_arrival) / ((1+0.16) ** grid_arrival - 1)
    d = 1/ ((1+ 0.16) ** grid_arrival)
    return  crf, d

folder = "../simulation_results/"
path = "./Nigeria_EnergyData_Plateau.csv"
data_set_ids = pd.read_csv(path, sep=';')


grid_arrival = 5
crf_t, d_t = get_crf(5)
crf_20, d_20 = get_crf(20)


############ GET add Branch distances #############


distances = pd.DataFrame([data_set_ids["Branch_id"].values, data_set_ids["Distance_m"].values/1000, data_set_ids["Distance_m"].values/1000, data_set_ids["Distance_m"].values/1000],
                         columns = data_set_ids.index,
                         index=['branch_id', 'original_distance_km', 'max_smaller_distance_on_branch', 'add_distance_on_branch'])
branches = {}
theoretical_distance = 0
for item in data_set_ids.index:
    distances[item]['max_smaller_distance_on_branch']=0
    theoretical_distance += data_set_ids["Distance_m"][item]/1000
    # create branch number and change distance, if larger than existing
    if data_set_ids["Branch_id"][item] not in branches:
        branches.update({data_set_ids["Branch_id"][item]: data_set_ids["Distance_m"][item]/1000})
    else:
        if branches[data_set_ids["Branch_id"][item]] < data_set_ids["Distance_m"][item]/1000:
            branches.update({data_set_ids["Branch_id"][item]: data_set_ids["Distance_m"][item]/1000})

cost_branches = {}
for item in branches:
    cost_branches.update({item: (branches[item] * 20000 + 20000)/branches[item]})

for loc1 in distances.columns:
    for loc2 in distances.columns:
        if distances[loc1]['branch_id']==distances[loc2]['branch_id']:
            if distances[loc1]['original_distance_km'] >= distances[loc2]['original_distance_km']:
                pass
            elif distances[loc1]['original_distance_km'] != distances[loc2]['original_distance_km'] \
                    and distances[loc1]['original_distance_km'] > distances[loc2]['max_smaller_distance_on_branch']:
                distances[loc2]['max_smaller_distance_on_branch'] = distances[loc1]['original_distance_km']

total = 0
for loc in distances.columns:
    distances[loc]['add_distance_on_branch'] = distances[loc]['original_distance_km']- distances[loc]['max_smaller_distance_on_branch']
    total += distances[loc]['add_distance_on_branch']

ratio = 2887/total

for prefix in ['reliable_', 'unreliable_']:
    number = -1

    folder_list = ["no_mgs",
                   "stage1_mgs",
                   "stage2_mgs",
                   "stage3_mgs"
                   ]


    columns=['Peak demand [kW]', 'Peak demand NESP [kW]', 'Peak demand diff [%]',
             'PV tool [kWp]', 'PV NESP [kWp]', 'PV diff [%]',
             'Storage tool [kW]', 'Storage tool [kWh]', 'Storage NESP [kWh]', 'Storage diff [%]',
             'Genset tool [kW]', 'Genset NESP [kW]', 'Genset diff [%]',
             'Cost transformers [kUSD]', 'Cost extension [kUSD]',
             'RES [%]', 'Supply reliability extension [%]', 'Customers [-]', 'Population [-]', 'Distance to national grid [km]', 'Additional branch distance [km]',
             'LCOE [USD/kWh]', 'NPV [kUSD]', 'NPV/HH [USD/HH]', 'NPV/kW [USD/kW]',
             'LCOE extension [USD/kWh]', 'NPV extension [kUSD]', 'NPV/HH extension [USD/HH]', 'NPV/kW extension [USD/kW]'
             ]
    capacities = pd.DataFrame(columns=columns)

    column_list_per_stage_totals = ['PV tool total [kWp]', 'PV NESP total [kWp]',
                                    'Storage tool total [kWh]', 'Storage tool total [kW]', 'Storage NESP total [kWh]',
                                    'Genset tool total [kW]', 'Genset NESP total [kW]',
                                    'NPV total [kUSD]']

    column_list_per_stage_vars = []
    for item in columns:
        column_list_per_stage_vars = column_list_per_stage_vars + [item + postfix for postfix in [' average', ' min', ' max', ' std']]

    column_list_per_stage = column_list_per_stage_totals + column_list_per_stage_vars

    per_stage = pd.DataFrame(index=folder_list, columns=column_list_per_stage)

    for file in folder_list:
        data = pd.read_csv(folder + "/results_" + prefix + file + ".csv", sep=',')

        name_list = []
        for item in data.index:
            if data['project_site_name'][item] not in name_list:
                name_list.append(data['project_site_name'][item])

        capacities_stage = pd.DataFrame(index=name_list, columns=columns)
        for item in data.index:
            if data['case'][item] == 'offgrid_mg':
                capacities_stage['Peak demand [kW]'][data['project_site_name'][item]]     = data['demand_peak_kW'][item]
                capacities_stage['PV tool [kWp]'][data['project_site_name'][item]]        = data['capacity_pv_kWp'][item]
                capacities_stage['Storage tool [kWh]'][data['project_site_name'][item]]   = data['capacity_storage_kWh'][item]
                capacities_stage['Storage tool [kW]'][data['project_site_name'][item]]    = data['power_storage_kW'][item]
                capacities_stage['Genset tool [kW]'][data['project_site_name'][item]]     = data['capacity_genset_kW'][item]
                capacities_stage['RES [%]'][data['project_site_name'][item]] = data['res_share'][item] * 100
                capacities_stage['LCOE [USD/kWh]'][data['project_site_name'][item]] = data['lcoe'][item]
                capacities_stage['NPV [kUSD]'][data['project_site_name'][item]] = data['npv'][item]/1000
                capacities_stage['NPV/kW [USD/kW]'][data['project_site_name'][item]] = capacities_stage['NPV [kUSD]'][data['project_site_name'][item]]/data['demand_peak_kW'][item] * 1000

            if data['case'][item] == 'sole_maingrid':
                capacities_stage['LCOE extension [USD/kWh]'][data['project_site_name'][item]] \
                    = data['lcoe'][item]
                capacities_stage['Cost extension [kUSD]'][data['project_site_name'][item]] \
                    = data['costs_maingrid_extension'][item] / 1000
                capacities_stage['Cost transformers [kUSD]'][data['project_site_name'][item]] \
                    = data['costs_pcoupling'][item] / 1000

                capacities_stage['Supply reliability extension [%]'][data['project_site_name'][item]] \
                    = data['supply_reliability_kWh'][item]
                capacities_stage['NPV extension [kUSD]'][data['project_site_name'][item]] \
                    = data['npv'][item] / 1000
                capacities_stage['NPV/kW extension [USD/kW]'][data['project_site_name'][item]]\
                    = capacities_stage['NPV extension [kUSD]'][data['project_site_name'][item]] / data['demand_peak_kW'][item] * 1000

        for item in data_set_ids.index:
            name = "nesp_" + str(data_set_ids['NESP_ID'][item])
            if name in name_list:
                capacities_stage['Additional branch distance [km]'][name] = distances[item]['add_distance_on_branch'] * ratio
                capacities_stage['Distance to national grid [km]'][name] = data_set_ids['Distance_m'][item]/1000
                capacities_stage['Peak demand NESP [kW]'][name] = data_set_ids['Demand'][item]
                capacities_stage['Customers [-]'][name] = data_set_ids['Customers'][item]
                capacities_stage['Population [-]'][name] = data_set_ids['Population'][item]
                capacities_stage['PV NESP [kWp]'][name]          = data_set_ids['PV size(kW)'][item]
                capacities_stage['Storage NESP [kWh]'][name]     = data_set_ids['Battery capacity (kWh)'][item]
                capacities_stage['Genset NESP [kW]'][name]       = data_set_ids['Generator capacity (kw)'][item]
                capacities_stage['NPV/HH [USD/HH]'][name] = \
                    capacities_stage['NPV [kUSD]'][name] / data_set_ids['Customers'][item] * 1000
                capacities_stage['NPV/HH extension [USD/HH]'][name] = \
                    capacities_stage['NPV extension [kUSD]'][name] / data_set_ids['Customers'][item] * 1000

        capacities_stage['Peak demand diff [%]'] = (capacities_stage['Peak demand [kW]'] - capacities_stage['Peak demand NESP [kW]'] ) / \
                                                     capacities_stage['Peak demand NESP [kW]']

        capacities_stage['PV diff [%]'] = \
            (capacities_stage['PV tool [kWp]'] - capacities_stage['PV NESP [kWp]']) / capacities_stage['PV NESP [kWp]'] * 100
        capacities_stage['Storage diff [%]'] = \
            (capacities_stage['Storage tool [kWh]'] - capacities_stage['Storage NESP [kWh]']) / capacities_stage['Storage NESP [kWh]'] * 100
        capacities_stage['Genset diff [%]'] = \
            (capacities_stage['Genset tool [kW]'] - capacities_stage['Genset NESP [kW]']) / capacities_stage['Genset NESP [kW]'] * 100

        per_stage['PV tool total [kWp]'][file]        = capacities_stage['PV tool [kWp]'].sum()
        per_stage['PV NESP total [kWp]'][file]        = capacities_stage['PV NESP [kWp]'].sum()

        per_stage['Storage tool total [kWh]'][file]   = capacities_stage['Storage tool [kWh]'].sum()
        per_stage['Storage tool total [kW]'][file]   = capacities_stage['Storage tool [kW]'].sum()
        per_stage['Storage NESP total [kWh]'][file]   = capacities_stage['Storage NESP [kWh]'].sum()

        per_stage['Genset tool total [kW]'][file]     = capacities_stage['Genset tool [kW]'].sum()
        per_stage['Genset NESP total [kW]'][file]     = capacities_stage['Genset NESP [kW]'].sum()

        per_stage['NPV total [kUSD]'][file] = capacities_stage['NPV [kUSD]'].sum()

        for item in columns:
            per_stage = add_statistics(per_stage, capacities_stage, item, file)

        capacities_stage['Diff NPV/kW [USD/kW]'] = capacities_stage['NPV/kW [USD/kW]'].values - capacities_stage['NPV/kW extension [USD/kW]'].values
        capacities_stage['Diff NPV/HH [USD/HH]'] = capacities_stage['NPV/HH [USD/HH]'].values - capacities_stage['NPV/HH extension [USD/HH]'].values
        capacities_stage['Diff NPV [kUSD]'] = capacities_stage['NPV [kUSD]'].values - capacities_stage['NPV extension [kUSD]'].values
        capacities_stage['Diff LCOE [USD/kWh]'] = capacities_stage['LCOE [USD/kWh]'].values - capacities_stage['LCOE extension [USD/kWh]']

        capacities_stage['Relative diff NPV/kW [USD/kW]'] = \
            capacities_stage['Diff NPV/kW [USD/kW]'].values / capacities_stage['NPV/kW [USD/kW]'].values

        capacities_stage['Relative diff NPV/HH [USD/HH]'] = \
            capacities_stage['Diff NPV/HH [USD/HH]'].values / capacities_stage['NPV/HH [USD/HH]'].values

        capacities_stage['Relative diff NPV [kUSD]'] = \
            capacities_stage['Diff NPV [kUSD]'].values / capacities_stage['NPV [kUSD]'].values

        capacities_stage['Relative diff LCOE [USD/kWh]'] = \
            capacities_stage['Diff LCOE [USD/kWh]'].values / capacities_stage['LCOE [USD/kWh]'].values

        if file == "stage1_mgs":
            stage1 = capacities_stage.copy()
        elif file == "stage2_mgs":
            stage2 = capacities_stage.copy()
        elif file == "stage3_mgs":
            stage3 = capacities_stage.copy()
        elif file == "no_mgs":
            no_mgs = capacities_stage.copy()

        capacities = capacities.append(capacities_stage, sort=False)

    number = plot_matrix(capacities, number, 'LCOE [USD/kWh]')

    plots = pd.DataFrame([capacities[name].values for name in ['Additional branch distance [km]', 'Distance to national grid [km]', 'Peak demand [kW]']],
                         index=['Additional branch distance [km]', 'Distance to national grid [km]',  'Peak demand [kW]']).transpose()
    for column in plots.columns:
        q = plots[column].quantile(0.90)
        plots = plots[plots[column] < q]

    number = number + 1
    fig = plots.plot.hexbin(x='Additional branch distance [km]', y='Peak demand [kW]', colormap='viridis', gridsize=15)
    fig.set(title="Distribution of project sites")
    plt.savefig(folder + "evaluation/" + 'graph_' + prefix + str(number) +'.png', bbox_inches="tight")

    number = number + 1
    fig = plots.plot.hexbin(x='Distance to national grid [km]', y='Peak demand [kW]', colormap='viridis', gridsize=15)
    fig.set(title="Distribution of project sites")
    plt.savefig(folder + "evaluation/" + 'graph_' + prefix + str(number) +'.png', bbox_inches="tight")

    capacities_file = add_statistics_matrix(capacities)
    per_stage = add_statistics_matrix(per_stage)

    per_stage.to_csv(folder + "evaluation/" + "nesp_comparison_" + prefix + "stages.csv")
    capacities_file.to_csv(folder + "evaluation/" + "/nesp_comparison_" + prefix[:-1] + ".csv")

    comparison_list_y = ['LCOE [USD/kWh]',
                         'NPV/HH [USD/HH]',
                         'Genset diff [%]',
                         'Storage diff [%]',
                         'PV diff [%]',
                         'RES [%]',
                         'NPV/kW [USD/kW]',
                         #'Relative diff NPV/kW [USD/kW]',
                         #'Relative diff NPV/HH [USD/HH]',
                         #'Relative diff NPV [kUSD]',
                         'Relative diff LCOE [USD/kWh]']
    comparison_list_x = ['Peak demand [kW]',
                         'Distance to national grid [km]',
                         'Additional branch distance [km]',
                         'Customers [-]']

    number = plot_x_y_stages(comparison_list_x, comparison_list_y, stage1, stage2, stage3, no_mgs, number)

    ########## ASPECT 2 ##################
    title_costs = ['LCOE [USD/kWh]', 'NPV [kUSD]', 'NPV/HH [USD/HH]', 'NPV/kW [USD/kW]', 'Autonomy [%]']
    list_cases = ['offgrid_mg', 'sole_maingrid', 'offgrid_mg_cons', 'offgrid_mg_cons_prod', 'ongrid_mg_cons', 'ongrid_mg_cons_prod', 'reimbursement', 'abandonment', 'spp', 'spd']

    costs_titles = ['Peak demand [kW]',
                    'Customers [-]',
                    'Distance to national grid [km]',
                    'Additional branch distance [km]',
                    'annual demand [kWh/a]',
                    'Grid extension incl pcc [USD]',
                    'PV CAP',
                    'MG costs until grid arrival [USD]',
                    'abandonment [USD]',
                    'profit loss at termination [USD]',
                    'spd abandonement [USD]',
                    'spd future operation costs [USD]',
                    'spp solar generation [MWh/a]',
                    'spp solar generation [MWh/a/kWp]',
                    'spp upgrade costs [USD]',
                    'spp abandonement [USD]',
                    'spp future operation costs [USD]',
                    'reimbursement distribution grid [USD]',
                    'reimbursement all equipment [USD]'
                    ]

    for item in title_costs:
        costs_titles = costs_titles + [item + ' ' + postfix for postfix in list_cases]

    costs = pd.DataFrame(columns = costs_titles)

    case_list_aspect1 = ['offgrid_mg', 'sole_maingrid']

    if prefix == 'unreliable_':
        case_list_aspect2_on_off = ['offgrid_mg', 'offgrid_mg_cons', 'offgrid_mg_cons_prod']
        case_list_aspect2_on = ['offgrid_mg_cons', 'offgrid_mg_cons_prod']
        case_list_aspect3_on_off = ['offgrid_mg', 'offgrid_mg_cons', 'offgrid_mg_cons_prod', 'ongrid_mg_cons',
                                    'ongrid_mg_cons_prod']
        case_list_aspect3_on = ['offgrid_mg_cons_prod', 'ongrid_mg_cons', 'ongrid_mg_cons_prod']
    else:
        case_list_aspect2_on_off = ['offgrid_mg', 'sole_maingrid', 'offgrid_mg_cons', 'offgrid_mg_cons_prod']
        case_list_aspect2_on = ['sole_maingrid', 'offgrid_mg_cons', 'offgrid_mg_cons_prod']
        case_list_aspect3_on_off = ['offgrid_mg', 'sole_maingrid', 'offgrid_mg_cons', 'offgrid_mg_cons_prod',
                                    'ongrid_mg_cons', 'ongrid_mg_cons_prod']
        case_list_aspect3_on = ['offgrid_mg_cons_prod', 'ongrid_mg_cons', 'ongrid_mg_cons_prod']

    case_list_aspect3_all = ['offgrid_mg_cons', 'offgrid_mg_cons_prod', 'ongrid_mg_cons', 'ongrid_mg_cons_prod', 'reimbursement', 'abandonment', 'spp', 'spd']
    case_list_aspect3_adapt = ['offgrid_mg_cons', 'offgrid_mg_cons_prod', 'reimbursement', 'abandonment', 'spp', 'spd']


    number_of_favoured = pd.DataFrame(index=folder_list, columns=list_cases)
    for i in number_of_favoured.index:
        for j in number_of_favoured.columns:
            number_of_favoured[j][i] = 0

    number_of_favoured_aspect1 = number_of_favoured[case_list_aspect1].copy()
    number_of_favoured_aspect2_on_off = number_of_favoured[case_list_aspect2_on_off].copy()
    number_of_favoured_aspect2_on = number_of_favoured[case_list_aspect2_on].copy()
    number_of_favoured_aspect3_on_off = number_of_favoured[case_list_aspect3_on_off].copy()
    number_of_favoured_aspect3_on = number_of_favoured[case_list_aspect3_on].copy()
    number_of_favoured_aspect3_npv = number_of_favoured[case_list_aspect3_all].copy()
    number_of_favoured_aspect3_lcoe = number_of_favoured[case_list_aspect3_all].copy()
    number_of_favoured_aspect3_adapt_lcoe = number_of_favoured[case_list_aspect3_adapt].copy()

    for file in folder_list:
        data = pd.read_csv(folder + "/results_" + prefix + file + ".csv", sep=',')

        name_list = []
        for item in data.index:
            if data['project_site_name'][item] not in name_list:
                name_list.append(data['project_site_name'][item])

        costs_stage = pd.DataFrame(index=name_list, columns=costs_titles)

        for item in data_set_ids.index:
            name = "nesp_" + str(data_set_ids['NESP_ID'][item])
            if name in name_list:
                costs_stage['Additional branch distance [km]'][name] = distances[item]['add_distance_on_branch'] * ratio
                costs_stage['Customers [-]'][name] = data_set_ids['Customers'][item]
                costs_stage['Distance to national grid [km]'][name] = data_set_ids['Distance_m'][item] / 1000
                generation = pd.read_csv('../inputs/timeseries/'+name+'.csv', sep=';')
                costs_stage['spp solar generation [MWh/a/kWp]'][name] = generation['SolarGen'].sum()

        for item in data.index:
            if data['case'][item] in list_cases:
                costs_stage['Autonomy [%] ' + data['case'][item]][data['project_site_name'][item]] = data['autonomy_factor'][item]
                costs_stage['Peak demand [kW]'][data['project_site_name'][item]] = data['demand_peak_kW'][item]
                costs_stage['annual demand [kWh/a]'][data['project_site_name'][item]] = data['total_demand_annual_kWh'][item]
                costs_stage['LCOE [USD/kWh] ' + data['case'][item]][data['project_site_name'][item]] = data['lcoe'][item]
                costs_stage['NPV [kUSD] ' + data['case'][item]][data['project_site_name'][item]] = data['npv'][item]/1000
                costs_stage['NPV/kW [USD/kW] ' + data['case'][item]][data['project_site_name'][item]] = \
                    costs_stage['NPV [kUSD] ' + data['case'][item]][data['project_site_name'][item]]/data['demand_peak_kW'][item] * 1000
                costs_stage['NPV/HH [USD/HH] ' + data['case'][item]][data['project_site_name'][item]] = \
                    costs_stage['NPV [kUSD] ' + data['case'][item]][data['project_site_name'][item]]/ costs_stage['Customers [-]'][data['project_site_name'][item]] * 1000

                costs_stage['spd future operation costs [USD]'][data['project_site_name'][item]] = 0
                costs_stage['spp future operation costs [USD]'][data['project_site_name'][item]] = 0

                if data['case'][item] == 'sole_maingrid':
                    costs_stage['Grid extension incl pcc [USD]'][data['project_site_name'][item]] = \
                        (data['annuity_maingrid_extension'][item] + data['annuity_pcoupling'][item])* d_t * (1/crf_20 - 1/crf_t)

                    costs_stage['spp upgrade costs [USD]'][data['project_site_name'][item]] = \
                        data['annuity_pcoupling'][item]* d_t * (1/crf_20 - 1/crf_t)

                if data['case'][item] == 'offgrid_mg':
                    costs_stage['PV CAP'][data['project_site_name'][item]] = data['capacity_pv_kWp'][item]

                    # sum up ALL annual costs until national grid arrival, including fuel
                    costs_stage['MG costs until grid arrival [USD]'][data['project_site_name'][item]] = data['annuity'][item] / crf_t

                    # get mg costs that occurr after grid arrives (assuming battery replacements!), ie.
                    # all npv minus the already paid annuities (including fuel costs) minus future fuel costs
                    # (add fuel costs until t to be able to substract full value
                    costs_stage['abandonment [USD]'][data['project_site_name'][item]] = \
                        (1 / crf_20 - 1 / crf_t) * data['annuity'][item]\
                        - (1 / crf_20 - 1 / crf_t) * data['expenditures_fuel_annual'][item]

                    # lost profit is revenue margin of sold electricity
                    costs_stage['profit loss at termination [USD]'][data['project_site_name'][item]] = \
                        data['total_demand_annual_kWh'][item]* (data['lcoe'][item]* 0.02) * d_t * (1 / crf_20 - 1 / crf_t)

                    # abandonement costs of spd differ, as distribution grid is further utilized!
                    costs_stage['spd abandonement [USD]'][data['project_site_name'][item]] = \
                        costs_stage['abandonment [USD]'][data['project_site_name'][item]]  \
                        - (data['annuity_distribution_grid'][item])* d_t *(crf_20 - crf_t)

                    costs_stage['spd future operation costs [USD]'][data['project_site_name'][item]] \
                        = costs_stage['spp future operation costs [USD]'][data['project_site_name'][item]]\
                        +  (data['annuity_distribution_grid'][item])* d_t *(1/crf_20 - 1/crf_t)

                    # abandonement costs of spp differ, as inverters and pv are further utilized!
                    costs_stage['spp abandonement [USD]'][data['project_site_name'][item]] = \
                        costs_stage['abandonment [USD]'][data['project_site_name'][item]]\
                        - (data['annuity_inverter_dc_ac'][item] + data['annuity_pv'][item]) * d_t * (1/crf_20 - 1/crf_t)

                    costs_stage['spp future operation costs [USD]'][data['project_site_name'][item]] \
                        = costs_stage['spp future operation costs [USD]'][data['project_site_name'][item]] + \
                          + (data['annuity_inverter_dc_ac'][item] + data['annuity_pv'][item]) * d_t *  (1/crf_20 - 1/crf_t)

                    # present value of reimbursement of distribution cost - annuities until arrival paid, rest value
                    costs_stage['reimbursement distribution grid [USD]'][data['project_site_name'][item]] = \
                        +  (data['annuity_distribution_grid'][item]) * d_t * (1/crf_20 - 1/crf_t)

                    # present value of reimbursement of all equipment cost - annuities until arrival paid
                    # AND revenues for one year (not profit margin!)
                    costs_stage['reimbursement all equipment [USD]'][data['project_site_name'][item]] = \
                        (costs_stage['abandonment [USD]'][data['project_site_name'][item]]
                         + data['lcoe'][item] * data['total_demand_annual_kWh'][item] * 1.02) * d_t


        # (2) npv of reimbursement includes investment costs up till arrival and abandonment costs which are equalled out by reimbursement
        costs_stage['NPV [kUSD] reimbursement'] = costs_stage['MG costs until grid arrival [USD]'] \
                                                  + costs_stage['abandonment [USD]'] \
                                                  - costs_stage['reimbursement all equipment [USD]']

        costs_stage['spp solar generation [MWh/a]'] = costs_stage['spp solar generation [MWh/a/kWp]'] * costs_stage['PV CAP']/1000
        costs_stage['spp feed-in [USD/a]'] = costs_stage['spp solar generation [MWh/a]'] * 0.05 * 1000
        costs_stage['spp future operation costs [USD]'] = costs_stage['spp future operation costs [USD]'] + costs_stage['spp upgrade costs [USD]']
        # (3) npv of spp includes investments until now, abandonment costs, reimbursements for distribution grid and solar feed-in over the next years.
        costs_stage['NPV [kUSD] spp'] = costs_stage['MG costs until grid arrival [USD]'] \
                    + costs_stage['spp abandonement [USD]'] \
                    - costs_stage['reimbursement distribution grid [USD]'] \
                    + costs_stage['spp future operation costs [USD]']\
                    - costs_stage['spp feed-in [USD/a]'] * d_t * (1/crf_20-1/crf_t)

        # (4) abandonment mg is operated until grid arrives, then terminated
        costs_stage['NPV [kUSD] abandonment'] = costs_stage['MG costs until grid arrival [USD]'] \
                                                    + costs_stage['abandonment [USD]'] \
                                                    #+ costs_stage['profit loss at termination [USD]']

        # (5) npv of spd includes investments until now, abandonment costs of all generation units, continued
        # operation of distribution grid and retail margin over the following years
        costs_stage['NPV [kUSD] spd'] = costs_stage['MG costs until grid arrival [USD]'] \
                                             + costs_stage['spd abandonement [USD]'] \
                                             + costs_stage['spd future operation costs [USD]'] \
                                             - costs_stage['annual demand [kWh/a]'] * (0.08 * 0.02) * d_t * (1/crf_20-1/crf_t)

        for item in ['reimbursement', 'abandonment', 'spp', 'spd']:
            costs_stage['NPV [kUSD] ' + item] = costs_stage['NPV [kUSD] ' + item] / 1000
            costs_stage['NPV [kUSD] ' + item] = costs_stage['NPV [kUSD] ' + item] + costs_stage['Grid extension incl pcc [USD]']/1000
            costs_stage['NPV/kW [USD/kW] '+item] = costs_stage['NPV [kUSD] '+item] / costs_stage['Peak demand [kW]']*1000
            costs_stage['NPV/HH [USD/HH] ' + item] = costs_stage['NPV [kUSD] ' + item] / costs_stage['Customers [-]'] * 1000
            costs_stage['LCOE [USD/kWh] '+item] = costs_stage['NPV [kUSD] '+item]*crf_t/costs_stage['annual demand [kWh/a]']*1000

        favoured = pd.DataFrame(index=costs_stage.index)
        favoured, number_of_favoured_aspect1  \
            = compare_solutions(costs_stage, favoured, number_of_favoured_aspect1, 'favoured_aspect1', case_list_aspect1, 'LCOE [USD/kWh] ')

        favoured, number_of_favoured_aspect2_on_off \
            = compare_solutions(costs_stage, favoured, number_of_favoured_aspect2_on_off, 'favoured_aspect2_on_off', case_list_aspect2_on_off, 'LCOE [USD/kWh] ')

        favoured, number_of_favoured_aspect2_on \
            = compare_solutions(costs_stage, favoured, number_of_favoured_aspect2_on, 'favoured_aspect2_on_off_npv_kW', case_list_aspect2_on,
                                'NPV/kW [USD/kW] ')

        favoured, number_of_favoured_aspect3_on_off \
            = compare_solutions(costs_stage, favoured, number_of_favoured_aspect3_on_off, 'favoured_aspect2_on', case_list_aspect3_on_off, 'LCOE [USD/kWh] ')

        favoured, number_of_favoured_aspect3_on \
            = compare_solutions(costs_stage, favoured, number_of_favoured_aspect3_on, 'favoured_aspect3_on_off', case_list_aspect3_on, 'LCOE [USD/kWh] ')

        favoured, number_of_favoured_aspect3_npv \
            = compare_solutions(costs_stage, favoured, number_of_favoured_aspect3_npv, 'favoured_aspect3_all_npv_kw', case_list_aspect3_all, 'NPV/kW [USD/kW] ')

        favoured, number_of_favoured_aspect3_lcoe \
            = compare_solutions(costs_stage, favoured, number_of_favoured_aspect3_lcoe, 'favoured_aspect3_all_lcoe', case_list_aspect3_all, 'LCOE [USD/kWh] ')

        favoured, number_of_favoured_aspect3_adapt_lcoe \
            = compare_solutions(costs_stage, favoured, number_of_favoured_aspect3_adapt_lcoe, 'favoured_aspect3_adapt_lcoe', case_list_aspect3_adapt, 'LCOE [USD/kWh] ')
        #print(favoured)
        #print(number_of_favoured_aspect3_adapt_lcoe)

        if file == "stage1_mgs":
            costs_stage1 = costs_stage.copy()
        elif file == "stage2_mgs":
            costs_stage2 = costs_stage.copy()
        elif file == "stage3_mgs":
            costs_stage3 = costs_stage.copy()
        elif file == "no_mgs":
            costs_no_mgs = costs_stage.copy()

        costs_stage = add_statistics_matrix(costs_stage)
        for column in favoured.columns:
            costs_stage[column] = favoured[column]
        costs = costs.append(costs_stage.drop(['min', 'max', 'average', 'sum']), sort=False)
        costs_stage.to_csv(folder + "evaluation/" + "costs_" + file + prefix[:-1] + ".csv")

    name_list = favoured.columns
    add_sum_save(number_of_favoured_aspect1, name_list[0])
    add_sum_save(number_of_favoured_aspect2_on_off, name_list[1])
    add_sum_save(number_of_favoured_aspect2_on, name_list[2])
    add_sum_save(number_of_favoured_aspect3_on_off, name_list[3])
    add_sum_save(number_of_favoured_aspect3_on, name_list[4])
    add_sum_save(number_of_favoured_aspect3_npv, name_list[5])
    add_sum_save(number_of_favoured_aspect3_lcoe, name_list[6])
    add_sum_save(number_of_favoured_aspect3_adapt_lcoe, name_list[7])

    favoured = costs[[item for item in favoured.columns]]
    costs = costs.drop([item for item in favoured.columns], axis=1)
    costs_file = add_statistics_matrix(costs)
    for column in favoured.columns:
        costs_file[column] = favoured[column]

    costs_file.to_csv(folder + "evaluation/" + "costs_all_solutions_" + prefix[:-1] + ".csv")

    color_dict = {'LCOE [USD/kWh] offgrid_mg': '#33ff00',
                  'LCOE [USD/kWh] sole_maingrid': '#000000',
                  'LCOE [USD/kWh] offgrid_mg_cons': '#0033cc',
                  'LCOE [USD/kWh] offgrid_mg_cons_prod': '#990099',
                  'LCOE [USD/kWh] ongrid_mg_cons': '#ffcc00',
                  'LCOE [USD/kWh] ongrid_mg_cons_prod': '#ffcc00',
                  'LCOE [USD/kWh] reimbursement': '#cc0000',
                  'LCOE [USD/kWh] spp': '#cc3300',
                  'LCOE [USD/kWh] spd': '#cc0033',
                  'LCOE [USD/kWh] abandonment': '#cc0099'}

    comparison_list_y = ['LCOE [USD/kWh] ' + item for item in list_cases]

    comparison_list_x = ['Peak demand [kW]',
                         'Distance to national grid [km]',
                         'Additional branch distance [km]',
                         'Customers [-]']

    number = plot_x_y_stages(comparison_list_x, comparison_list_y, costs_stage1, costs_stage2, costs_stage3, costs_no_mgs, number)

    comparison_list = comparison_list_x + comparison_list_y
    plots = pd.DataFrame([costs[name].values for name in comparison_list], index=comparison_list).transpose()

    for x in comparison_list_x:
        plotting = 0
        number += 1
        for y in comparison_list_y:
            if plotting == 0:
                fig = plots.plot.scatter(x=x, y=y, label=y[15:], color=color_dict[y]) # s=df['c'] * 200 plot THREE VALUES
                plotting = 1
            else:
                plots.plot.scatter(x=x, y=y, ax=fig, label=y[15:], color=color_dict[y])
        fig.set(ylabel='LCOE [USD/kWh]')
        fig.legend(loc='center left', bbox_to_anchor=(1, 0.5), frameon=False)
        plt.savefig(folder + "evaluation/" + 'graph_' + prefix + str(number) + '.png', bbox_inches="tight")
        plt.close()

    for y in comparison_list_y:
        number = plot_matrix(costs, number, y)

