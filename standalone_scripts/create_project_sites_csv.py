import pandas as pd
import os

path = "/home/local/RL-INSTITUT/martha.hoffmann/Desktop/Nextcloud/Masterthesis/Nigeria_Data/Nigeria_EnergyData_Plateau.csv"
data_set_ids = pd.read_csv(path, sep=';')
print (data_set_ids.columns)

demand_mg_s1 = pd.DataFrame(index=['project_site_name', 'timeseries_file', 'title_time', 'title_demand_ac', 'title_demand_dc', 'title_pv', 'title_wind', 'title_grid_availability', 'seperator', 'distribution_grid_cost_investment', 'distribution_grid_cost_opex', 'maingrid_distance'])
demand_mg_s2 = pd.DataFrame(index=['project_site_name', 'timeseries_file', 'title_time', 'title_demand_ac', 'title_demand_dc', 'title_pv', 'title_wind', 'title_grid_availability', 'seperator', 'distribution_grid_cost_investment', 'distribution_grid_cost_opex', 'maingrid_distance'])
demand_mg_s3 = pd.DataFrame(index=['project_site_name', 'timeseries_file', 'title_time', 'title_demand_ac', 'title_demand_dc', 'title_pv', 'title_wind', 'title_grid_availability', 'seperator', 'distribution_grid_cost_investment', 'distribution_grid_cost_opex', 'maingrid_distance'])
demand_no_mg = pd.DataFrame(index=['project_site_name', 'timeseries_file', 'title_time', 'title_demand_ac', 'title_demand_dc', 'title_pv', 'title_wind', 'title_grid_availability', 'seperator', 'distribution_grid_cost_investment', 'distribution_grid_cost_opex', 'maingrid_distance'])


branches = {}
theoretical_distance = 0
for item in data_set_ids.index:
    theoretical_distance += data_set_ids["Distance_m"][item]/1000
    if data_set_ids["Branch_id"][item] not in branches:
        branches.update({data_set_ids["Branch_id"][item]: data_set_ids["Distance_m"][item]/1000})
    else:
        if branches[data_set_ids["Branch_id"][item]] < data_set_ids["Distance_m"][item]/1000:
            branches.update({data_set_ids["Branch_id"][item]: data_set_ids["Distance_m"][item]/1000})

total_distance = 0
for item in branches:
    total_distance += branches[item]

ratio = total_distance/theoretical_distance

print('Total number of branches: ' + str(len(branches)))
print('Total distance covered by branches (km): ' + str(total_distance))
print('Theoretical distance covered by branches (km): ' + str(theoretical_distance))

for item in data_set_ids.index:
    file_path = '../inputs/timeseries/nesp_' + str(data_set_ids["NESP_ID"][item]) + '.csv'
    file_path_csv = 'nesp_' + str(data_set_ids["NESP_ID"][item]) + '.csv'
    if os.path.isfile(file_path):
        distribution_grid_costs_investment = data_set_ids["Customers"][item] * 400
        distribution_grid_costs_om = 0.01 * distribution_grid_costs_investment
        if data_set_ids['Electr_type_phase_1'][item] == 'mini-grid':
            demand_mg_s1[item]=['nesp_' + str(data_set_ids["NESP_ID"][item]), file_path_csv, 'None', 'Demand', 'None',
                                'SolarGen', 'Wind', 'None', ',', distribution_grid_costs_investment, distribution_grid_costs_om, ratio*data_set_ids["Distance_m"][item]/1000]

        elif data_set_ids['Electr_type_phase_2'][item] == 'mini-grid':
            demand_mg_s2[item] = ['nesp_' + str(data_set_ids["NESP_ID"][item]), file_path_csv, 'None', 'Demand', 'None',
                                  'SolarGen', 'Wind', 'None', ',', distribution_grid_costs_investment, distribution_grid_costs_om, ratio*data_set_ids["Distance_m"][item]/1000]

        elif data_set_ids['Electr_type_phase_3'][item] == 'mini-grid':
            demand_mg_s3[item] = ['nesp_' + str(data_set_ids["NESP_ID"][item]), file_path_csv, 'None', 'Demand', 'None',
                                  'SolarGen', 'Wind', 'None', ',', distribution_grid_costs_investment, distribution_grid_costs_om, ratio*data_set_ids["Distance_m"][item]/1000]

        else:
            demand_no_mg[item] = ['nesp_' + str(data_set_ids["NESP_ID"][item]), file_path_csv, 'None', 'Demand', 'None',
                                  'SolarGen', 'Wind', 'None', ',', distribution_grid_costs_investment, distribution_grid_costs_om, ratio*data_set_ids["Distance_m"][item]/1000]

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