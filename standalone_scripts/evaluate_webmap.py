import pandas as pd
import matplotlib.pyplot as plt

#path = "/home/local/RL-INSTITUT/martha.hoffmann/Desktop/Nigeria_EnergyData-2.csv"
path = "/mnt/Storage/Documents/Studium/RLI/Masterthesis/Nigeria_Data/Nigeria_EnergyData_All_States.csv"
data_set = pd.read_csv(path, sep=',')

print (data_set.columns)

list_states = ['Niger', 'Ogun', 'Plateau', 'Cross River', 'Sokoto']

totals = pd.DataFrame(columns=list_states,
                      index=['Customers (k)', 'Demand (MW)', 'MG Customers (k)', 'MG Demand (MW)', 'PV size (MWp)', 'Battery capacity (MWh)', 'Generator capacity (MW)'])
for row in totals.index:
    for country in list_states:
        totals[country][row]=0

for row in data_set.index:
    totals[data_set['State'][row]]['Demand (MW)'] += data_set['Demand'][row]/1000

    if data_set['Electr_type_phase_1'][row]=='mini-grid' or data_set['Electr_type_phase_2'][row]=='mini-grid' or data_set['Electr_type_phase_2'][row]=='mini-grid':
        totals[data_set['State'][row]]['MG Demand (MW)'] += data_set['Demand'][row] / 1000
        totals[data_set['State'][row]]['PV size (MWp)'] += data_set['PV size(kW)'][row]/1000
        totals[data_set['State'][row]]['Battery capacity (MWh)'] += data_set['Battery capacity (kWh)'][row]/1000
        totals[data_set['State'][row]]['Generator capacity (MW)'] += data_set['Generator capacity (kw)'][row]/1000
        totals[data_set['State'][row]]['MG Customers (k)'] += data_set['Customers'][row] / 1000

    totals[data_set['State'][row]]['Customers (k)'] += data_set['Customers'][row]/1000
    #data_set['Distance_m'][row] = float(data_set['Distance_m'][row])

totals.to_csv("/mnt/Storage/Documents/Studium/RLI/Masterthesis/Nigeria_Data/Nigeria_EnergyData_values_per_state.csv")

#data_set[['Distance_m']] = data_set[['Distance_m']].astype(float)
data_set.plot.scatter(x='Distance_m', y='Customers')
data_set.plot.scatter(x='Distance_m', y='Demand')
data_set.plot.scatter(x='Demand', y='PV size(kW)')
data_set.plot.scatter(x='Demand', y='Battery capacity (kWh)')
data_set.plot.scatter(x='Demand', y='Generator capacity (kw)')
plt.show()