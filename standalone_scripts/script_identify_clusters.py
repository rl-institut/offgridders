import pandas as pd

path = "/home/local/RL-INSTITUT/martha.hoffmann/Desktop/Nigeria_EnergyData-2.csv"
data_set_ids = pd.read_csv(path, sep=';')

path = "/home/local/RL-INSTITUT/martha.hoffmann/rl-institut/05_Temp/Catherina/Martha/Model_final/Loads/high_tariff_new_nesp_id.csv"
data_set = pd.read_csv(path, sep=';').drop(columns=['load_ID'])


timeseries = pd.DataFrame(index=[i for i in range(0,8760)])

for item in data_set_ids.index:
    timeseries[data_set_ids["NESP_ID"][item]]=data_set[[str(data_set_ids["NESP_ID"][item])]]

timeseries.to_csv('./demand_profiles_nigeria_plateau.csv')
