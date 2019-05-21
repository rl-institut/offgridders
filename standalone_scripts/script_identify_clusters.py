import pandas as pd
import logging
import time

logging.info('Loading webmap data')
path = "/home/local/RL-INSTITUT/martha.hoffmann/Desktop/Nigeria/Nigeria_EnergyData_Plateau.csv"
webmap_data = pd.read_csv(path, sep=';')

logging.info('Loading internal demand profiles')
path = "/home/local/RL-INSTITUT/martha.hoffmann/Desktop/Nigeria_Data_from_Catherina/Model_final/Loads/high_tariff_new_nesp_id.csv"

demand_set = pd.read_csv(path, sep=';')
demand_ids = demand_set['load_ID']
demand_set = demand_set.drop(columns=['load_ID']).transpose()

timeseries = pd.DataFrame()
timeseries_only_mg = pd.DataFrame()
demand_output = pd.DataFrame(index = demand_ids.values, columns=['peak', 'sum'])

logging.info('Reordering demand profiles according to ids')
for item in webmap_data.index:
    for entry in range(0, len(demand_ids)):
        if demand_ids[entry] == webmap_data["NESP_ID"][item]:
            row = entry

    timeseries[webmap_data["NESP_ID"][item]]=demand_set[row].values
    demand_output['peak'][webmap_data["NESP_ID"][item]]=demand_set[row].values.max()
    demand_output['sum'][webmap_data["NESP_ID"][item]] = demand_set[row].values.sum()

    if webmap_data['Electr_type_phase_1'][item] == 'mini-grid' \
            or webmap_data['Electr_type_phase_2'][item] == 'mini-grid' \
            or webmap_data['Electr_type_phase_2'][item] == 'mini-grid':
        timeseries_only_mg[webmap_data["NESP_ID"][item]] = demand_set[row].values

logging.info('Saving demand profiles as csv')
timeseries.to_csv('./demand_profiles_nigeria_plateau.csv')
timeseries_only_mg.to_csv('./demand_profiles_nigeria_plateau_micro_grids.csv')

logging.info('Saving evaluation like load_output')
demand_output.to_csv('./demand_output.csv')