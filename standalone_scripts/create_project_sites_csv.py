import pandas as pd
import os

#path = "/home/local/RL-INSTITUT/martha.hoffmann/Desktop/Nigeria/Nigeria_EnergyData_Plateau.csv"
path = "./Nigeria_EnergyData_Plateau.csv"
data_set_ids = pd.read_csv(path, sep=';')

index = ['project_site_name', 'timeseries_file', 'title_time', 'title_demand_ac', 'title_demand_dc', 'title_pv', 'title_wind', 'title_grid_availability', 'seperator', 'distribution_grid_cost_investment', 'distribution_grid_cost_opex', 'maingrid_cost_investment']
demand_mg_s1 = pd.DataFrame(index = index)
demand_mg_s2 = pd.DataFrame(index = index)
demand_mg_s3 = pd.DataFrame(index = index)
demand_no_mg = pd.DataFrame(index = index)

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

distances.to_csv('Plateau_distances.csv')

print('Total number of branches: ' + str(len(branches)))
print('Total distance covered by branches (km): ' + str(total))
print('Theoretical distance covered by branches (km): 2887')

for item in data_set_ids.index:
    file_path = '../inputs/timeseries/nesp_' + str(data_set_ids["NESP_ID"][item]) + '.csv'
    file_path_csv = 'nesp_' + str(data_set_ids["NESP_ID"][item]) + '.csv'
    if os.path.isfile(file_path):
        distribution_grid_costs_investment = data_set_ids["Customers"][item] * 400
        distribution_grid_costs_om = 0.01 * distribution_grid_costs_investment
        maingrid_cost_investment = distances[item]['add_distance_on_branch'] * cost_branches[distances[item]['branch_id']] * ratio
        if data_set_ids['Electr_type_phase_1'][item] == 'mini-grid':
            demand_mg_s1[item]=['nesp_' + str(data_set_ids["NESP_ID"][item]), file_path_csv, 'None', 'Demand', 'None',
                                'SolarGen', 'Wind', 'None', ',', distribution_grid_costs_investment, distribution_grid_costs_om, maingrid_cost_investment]

        elif data_set_ids['Electr_type_phase_2'][item] == 'mini-grid':
            demand_mg_s2[item] = ['nesp_' + str(data_set_ids["NESP_ID"][item]), file_path_csv, 'None', 'Demand', 'None',
                                  'SolarGen', 'Wind', 'None', ',', distribution_grid_costs_investment, distribution_grid_costs_om, maingrid_cost_investment]

        elif data_set_ids['Electr_type_phase_3'][item] == 'mini-grid':
            demand_mg_s3[item] = ['nesp_' + str(data_set_ids["NESP_ID"][item]), file_path_csv, 'None', 'Demand', 'None',
                                  'SolarGen', 'Wind', 'None', ',', distribution_grid_costs_investment, distribution_grid_costs_om, maingrid_cost_investment]

        else:
            demand_no_mg[item] = ['nesp_' + str(data_set_ids["NESP_ID"][item]), file_path_csv, 'None', 'Demand', 'None',
                                  'SolarGen', 'Wind', 'None', ',', distribution_grid_costs_investment, distribution_grid_costs_om, maingrid_cost_investment]

    else:
        print('Timeseries for location ' + str(data_set_ids["NESP_ID"][item]) + ' missing!')


print('Total count of project sites: ' + str(item))
print('Total count of project sites: demand_mg_s1 ' + str(len(demand_mg_s1.columns)))
print('Total count of project sites: demand_mg_s2 ' + str(len(demand_mg_s2.columns)))
print('Total count of project sites: demand_mg_s3 ' + str(len(demand_mg_s3.columns)))
print('Total count of project sites: demand_no_mg ' + str(len(demand_no_mg.columns)))

demand_mg_s1 = demand_mg_s1.transpose()
demand_mg_s1.to_csv('./project_sites_mg_stage1_plateau.csv')

demand_mg_s2 = demand_mg_s2.transpose()
demand_mg_s2.to_csv('./project_sites_mg_stage2_plateau.csv')

demand_mg_s3 = demand_mg_s3.transpose()
demand_mg_s3.to_csv('./project_sites_mg_stage3_plateau.csv')

demand_no_mg = demand_no_mg.transpose()
demand_no_mg.to_csv('./project_sites_no_mg_plateau.csv')