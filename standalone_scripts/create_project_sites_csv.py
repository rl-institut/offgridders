import pandas as pd
import os

path = "/home/local/RL-INSTITUT/martha.hoffmann/Desktop/Nextcloud/Masterthesis/Nigeria_Data/Nigeria_EnergyData_Plateau.csv"
data_set_ids = pd.read_csv(path, sep=';')

demand_mg_s1 = pd.DataFrame(index=['project_site_name', 'timeseries_file', 'title_time', 'title_demand_ac', 'title_demand_dc', 'title_pv', 'title_wind', 'title_grid_availability', 'seperator'])
demand_mg_s2 = pd.DataFrame(index=['project_site_name', 'timeseries_file', 'title_time', 'title_demand_ac', 'title_demand_dc', 'title_pv', 'title_wind', 'title_grid_availability', 'seperator'])
demand_mg_s3 = pd.DataFrame(index=['project_site_name', 'timeseries_file', 'title_time', 'title_demand_ac', 'title_demand_dc', 'title_pv', 'title_wind', 'title_grid_availability', 'seperator'])
demand_no_mg = pd.DataFrame(index=['project_site_name', 'timeseries_file', 'title_time', 'title_demand_ac', 'title_demand_dc', 'title_pv', 'title_wind', 'title_grid_availability', 'seperator'])

for item in data_set_ids.index:
    file_path = '../inputs/timeseries/nesp_' + str(data_set_ids["NESP_ID"][item]) + '.csv'
    if os.path.isfile(file_path):
        if data_set_ids['Electr_type_phase_1'][item] == 'mini-grid':
            demand_mg_s1[item]=['nesp_' + str(data_set_ids["NESP_ID"][item]), file_path, 'None', 'Demand', 'None', 'SolarGen', 'Wind', 'None', ';']

        elif data_set_ids['Electr_type_phase_2'][item] == 'mini-grid':
            demand_mg_s2[item] = ['nesp_' + str(data_set_ids["NESP_ID"][item]), file_path, 'None', 'Demand', 'None',
                                  'SolarGen', 'Wind', 'None', ';']

        elif data_set_ids['Electr_type_phase_2'][item] == 'mini-grid':
            demand_mg_s3[item] = ['nesp_' + str(data_set_ids["NESP_ID"][item]), file_path, 'None', 'Demand', 'None',
                                  'SolarGen', 'Wind', 'None', ';']

        else:
            demand_no_mg[item] = ['nesp_' + str(data_set_ids["NESP_ID"][item]), file_path, 'None', 'Demand', 'None',
                                  'SolarGen', 'Wind', 'None', ';']

    else:
        print('Timeseries for location ' + str(data_set_ids["NESP_ID"][item]) + ' missing!')


print('Total count of project sites: ' + str(item))
demand_mg_s1 = demand_mg_s1.transpose()
demand_mg_s1.to_csv('./project_sites_mg_stage1_plateau.csv')

demand_mg_s2 = demand_mg_s2.transpose()
demand_mg_s2.to_csv('./project_sites_mg_stage2_plateau.csv')

demand_mg_s3 = demand_mg_s3.transpose()
demand_mg_s3.to_csv('./project_sites_mg_stage3_plateau.csv')

demand_no_mg = demand_no_mg.transpose()
demand_no_mg.to_csv('./project_sites_no_mg_plateau.csv')