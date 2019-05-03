import pandas as pd

list_of_files = {'T2': ['T2_ac_year_final', 'T2_dc_year_final'],
                 'T4': ['T4_ac_year_final', 'T4_dc_year_final']}


for file in list_of_files:
    ac = '../inputs/timeseries/'+list_of_files[file][0]+'.csv'
    dc = '../inputs/timeseries/'+list_of_files[file][0]+'.csv'
    ac_data = pd.read_csv(ac, sep=',')
    dc_data = pd.read_csv(dc, sep=',')
    ac_dc_data=ac_data.drop(['power'], axis=1)
    ac_dc_data['GridUnavailability'] = 1 - ac_data['GridAvailability'].values
    ac_dc_data['Demand AC'] = ac_data['power'].values * ac_data['GridAvailability'].values
    ac_dc_data['Demand DC'] = dc_data['power'].values * ac_dc_data['GridUnavailability'].values

    print(ac_dc_data)

    ac_dc_data.to_csv('../inputs/timeseries/'+file+'_ac_dc_year.csv')