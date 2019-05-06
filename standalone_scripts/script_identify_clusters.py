import pandas as pd

path = "/home/local/RL-INSTITUT/martha.hoffmann/Desktop/Nextcloud/Masterthesis/Nigeria_Data/Nigeria_EnergyData_Plateau.csv"
data_set_ids = pd.read_csv(path, sep=';')

path = "/home/local/RL-INSTITUT/martha.hoffmann/rl-institut/05_Temp/Catherina/Martha/Model_final/Loads/high_tariff_new_nesp_id.csv"
data_set = pd.read_csv(path, sep=';').drop(columns=['load_ID']).transpose()

print (len(data_set.columns))
print (len(data_set.index))

print (len(data_set_ids.columns))
print (len(data_set_ids.index))

timeseries = pd.DataFrame()
timeseries_only_mg = pd.DataFrame()

for item in data_set_ids.index:
    timeseries[data_set_ids["NESP_ID"][item]]=data_set[data_set_ids["NESP_ID"][item]].values
    if data_set_ids['Electr_type_phase_1'][item] == 'mini-grid' \
            or data_set_ids['Electr_type_phase_2'][item] == 'mini-grid' \
            or data_set_ids['Electr_type_phase_2'][item] == 'mini-grid':
        timeseries_only_mg[data_set_ids["NESP_ID"][item]] = data_set[data_set_ids["NESP_ID"][item]].values

print (len(timeseries.columns))
print (len(timeseries.index))

print (len(timeseries_only_mg.columns))
print (len(timeseries_only_mg.index))

timeseries.to_csv('./demand_profiles_nigeria_plateau.csv')
timeseries_only_mg.to_csv('./demand_profiles_nigeria_plateau_micro_grids.csv')