import pandas as pd
import os

result_folders = ['../sdg_leicester_ac', '../sdg_leicester_ac_main_grid', '../sdg_leicester_ac_dc', '../sdg_leicester_dc']

result_files = ['results_ac',  'results_ac_main_grid', 'results_ac_dc', 'results_dc']

all_data = pd.DataFrame()

for item in range(0, len(result_files)):
    path = result_folders[item] + '/' + result_files[item] + '.csv'
    path = os.path.abspath(path)
    data = pd.read_csv(path).drop(['Unnamed: 0'], axis=1)
    all_data = all_data.append(data)

all_data = pd.DataFrame(all_data.values, columns=all_data.columns, index=[i for i in range(0, len(all_data))])
all_data.to_csv('../overall_results_sdg.csv')

locations = ['Tier2_AC']
cases = ['sole_main_grid']

evaluation_parameters = ['lcoe', 'renewable_share']
sensitivity_parameters = {'shortage_max_allowed': 0}

all_data_locations = {}
# sort results by location
for location in locations:
    one_location = pd.DataFrame()
    for row in all_data.index:
        if all_data['project_site_name'][row]!=location and all_data['shortage_max_allowed'][row]!=sensitivity_parameters[]:
            one_location[]=all_data[evaluation_parameters]
    all_data_locations.update({location: one_location})

