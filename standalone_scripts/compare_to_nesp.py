import pandas as pd
import matplotlib as plt

folder = "../simulation_results/"

folder_list = [#"reliable_no_mgs",
               "reliable_stage1_mgs",
               "reliable_stage2_mgs",
               "reliable_stage3_mgs"
               #"shs_shortage_stage1_mgs",
               #"shs_shortage_stage2_mgs",
               #"shs_shortage_stage3_mgs",
               #"shs_stage1_mgs",
               #"shs_stage2_mgs",
               #"shs_stage3_mgs",
               #"unreliable_stage1_mgs",
               #"unreliable_stage2_mgs",
               #"unreliable_stage3_mgs"
               ]

path = "/home/local/RL-INSTITUT/martha.hoffmann/Desktop/Nigeria/Nigeria_EnergyData_Plateau.csv"
data_set_ids = pd.read_csv(path, sep=';')

columns=['Peak demand kW', 'Peak demand kW webmap', 'PV tool kWp', 'PV NESP kWp', 'PV diff [%]', 'Storage tool kWh', 'Storage NESP kWh', 'Storage diff [%]', 'Genset tool kW', 'Genset NESP kW', 'Genset diff [%]']
capacities = pd.DataFrame(columns=columns)

per_stage = pd.DataFrame(
    index=folder_list,
    columns=['PV tool total kWp', 'PV NESP total kWp', 'PV diff average [%]',
             'Storage tool total kWh', 'Storage NESP total kWh', 'Storage diff average [%]',
             'Genset tool total kW', 'Genset NESP total kW', 'Genset diff average [%]'])

print(per_stage)
for file in folder_list:
    data = pd.read_csv(folder + file + "/results_" + file + ".csv", sep=',')

    name_list = []
    for item in data.index:
        if data['project_site_name'][item] not in name_list:
            name_list.append(data['project_site_name'][item])

    capacities_stage = pd.DataFrame(index=name_list, columns=columns)
    for item in data.index:
        if data['case'][item] == 'offgrid_mg':
            capacities_stage['Peak demand kW'][data['project_site_name'][item]]     = data['demand_peak_kW'][item]
            capacities_stage['PV tool kWp'][data['project_site_name'][item]]        = data['capacity_pv_kWp'][item]
            capacities_stage['Storage tool kWh'][data['project_site_name'][item]]   = data['capacity_storage_kWh'][item]
            capacities_stage['Genset tool kW'][data['project_site_name'][item]]     = data['capacity_genset_kW'][item]

    for item in data_set_ids.index:
        name = "nesp_" + str(data_set_ids['NESP_ID'][item])
        if name in name_list:
            capacities_stage['Peak demand kW webmap'][name] = data_set_ids['Demand'][item]
            capacities_stage['PV NESP kWp'][name]          = data_set_ids['PV size(kW)'][item]
            capacities_stage['Storage NESP kWh'][name]     = data_set_ids['Battery capacity (kWh)'][item]
            capacities_stage['Genset NESP kW'][name]       = data_set_ids['Generator capacity (kw)'][item]

    capacities_stage['PV diff [%]'] = \
        (capacities_stage['PV tool kWp'] ) / capacities_stage['PV NESP kWp']
    capacities_stage['Storage diff [%]'] = \
        (capacities_stage['Storage tool kWh'] ) / capacities_stage['Storage NESP kWh']
    capacities_stage['Genset diff [%]'] = \
        (capacities_stage['Genset tool kW'] ) / capacities_stage['Genset NESP kW']

    per_stage['PV tool total kWp'][file]        = capacities_stage['PV tool kWp'].sum()
    per_stage['PV NESP total kWp'][file]        = capacities_stage['PV NESP kWp'].sum()
    per_stage['PV diff average [%]'][file]      = capacities_stage['PV diff [%]'].mean()
    per_stage['Storage tool total kWh'][file]   = capacities_stage['Storage tool kWh'].sum()
    per_stage['Storage NESP total kWh'][file]   = capacities_stage['Storage NESP kWh'].sum()
    per_stage['Storage diff average [%]'][file] = capacities_stage['Storage diff [%]'].mean()
    per_stage['Genset tool total kW'][file]     = capacities_stage['Genset tool kW'].sum()
    per_stage['Genset NESP total kW'][file]     = capacities_stage['Genset NESP kW'].sum()
    per_stage['Genset diff average [%]'][file]  = capacities_stage['Genset diff [%]'].mean()

    capacities = capacities.append(capacities_stage)

print(per_stage)
capacities.to_csv("./results_nesp_comparison.csv")
#capacities.plot.scatter(x='Peak demand kW', y='PV diff [%]', title='PV diff [%]')
#capacities.plot.scatter(x='Peak demand kW', y='Storage diff [%]', title='Storage diff [%]')
#capacities.plot.scatter(x='Peak demand kW', y='Genset diff [%]', title='Genset diff [%]')
#plt.show()