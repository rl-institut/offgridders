import pandas as pd

list_of_files = ['T2_ac_week',
                 'T2_dc_week',
                 'T2_ac_dc_week',
                 'T4_ac_week',
                 'T4_dc_week',
                 'T4_ac_dc_week']

constant_data = pd.read_csv('../inputs/timeseries/'+'intermediate_tier2'+'.csv', sep=',')

for file in list_of_files:
    name = '../inputs/timeseries/'+file+'.csv'
    data = pd.read_csv(name, sep=',').drop(['hour', 'GridAvailability', 'SolarGen'], axis=1)
    new_data = data
    for i in range(0,52):
        new_data = new_data.append(data)

    new_data = new_data[0:8760]
    len(constant_data['GridAvailability'].values)
    new_data['GridAvailability'] = constant_data['GridAvailability'].values
    new_data['SolarGen'] = constant_data['SolarGen'].values

    new_data.to_csv('../inputs/timeseries/'+file[:-4]+'year.csv')