import pandas as pd
import matplotlib.pyplot as plt

folder = "../simulation_results/"

folder_list = [#"unreliable_stage1_mgs",
               #"unreliable_stage2_mgs",
               #"unreliable_stage3_mgs",
               #"unreliable_no_mgs"
               #"reliable_no_mgs",
               "reliable_stage1_mgs",
                "reliable_stage2_mgs",
               "reliable_stage3_mgs"
               #"shs_shortage_stage1_mgs",
               #"shs_shortage_stage2_mgs",
               #"shs_shortage_stage3_mgs",
               #"shs_stage1_mgs",
               #"shs_stage2_mgs",
               #"shs_stage3_mgs",
               ]

path = "./Nigeria_EnergyData_Plateau.csv"
data_set_ids = pd.read_csv(path, sep=';')

columns=['Peak demand kW', 'Peak demand kW webmap',
         'PV tool kWp', 'PV NESP kWp', 'PV diff [%]',
         'Storage tool kWh', 'Storage NESP kWh', 'Storage diff [%]',
         'Genset tool kW', 'Genset NESP kW', 'Genset diff [%]',
         'RES [%]', 'Customers',
         'LCOE [USD/kWh]', 'NPV [kUSD]', 'NPV/HH [USD/HH]', 'NPV/kW [USD/kW]',
          'LCOE extension [USD/kWh]', 'NPV extension [kUSD]', 'NPV/HH extension [USD/HH]', 'NPV/kW extension [USD/kW]'
         ]
capacities = pd.DataFrame(columns=columns)

per_stage = pd.DataFrame(
    index=folder_list,
    columns=['PV tool total kWp', 'PV NESP total kWp', 'PV diff average [%]', 'PV diff min [%]', 'PV diff max [%]',
             'Storage tool total kWh', 'Storage NESP total kWh', 'Storage diff average [%]', 'Storage diff min [%]', 'Storage diff max [%]',
             'Genset tool total kW', 'Genset NESP total kW', 'Genset diff average [%]', 'Genset diff min [%]', 'Genset diff max [%]',
             'RES average [%]', 'RES min [%]', 'RES max [%]',
             'LCOE average [USD/kWh]', 'LCOE min [USD/kWh]', 'LCOE max [USD/kWh]',
             'NPV average [kUSD]', 'NPV min [kUSD]', 'NPV max [kUSD]',
             'NPV/HH average [USD/HH]', 'NPV/HH min [USD/HH]', 'NPV/HH max [USD/HH]',
             'NPV/kW average [USD/kW]', 'NPV/kW min [USD/kW]', 'NPV/kW max [USD/kW]',
             'LCOE extension average [USD/kWh]', 'LCOE extension min [USD/kWh]', 'LCOE extension max [USD/kWh]',
             'NPV extension average [kUSD]', 'NPV extension min [kUSD]', 'NPV extension max [kUSD]',
             'NPV/HH extension average [USD/HH]', 'NPV/HH extension min [USD/HH]', 'NPV/HH extension max [USD/HH]',
             'NPV/kW extension average [USD/kW]', 'NPV/kW extension min [USD/kW]', 'NPV/kW extension max [USD/kW]'
             ])

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
            capacities_stage['RES [%]'][data['project_site_name'][item]] = data['res_share'][item] * 100
            capacities_stage['LCOE [USD/kWh]'][data['project_site_name'][item]] = data['lcoe'][item]
            capacities_stage['NPV [kUSD]'][data['project_site_name'][item]] = data['npv'][item]/1000
            capacities_stage['NPV/kW [USD/kW]'][data['project_site_name'][item]] = capacities_stage['NPV [kUSD]'][data['project_site_name'][item]]/data['demand_peak_kW'][item] * 1000

        if data['case'][item] == 'sole_maingrid':
            capacities_stage['LCOE extension [USD/kWh]'][data['project_site_name'][item]] \
                = data['lcoe'][item]
            capacities_stage['NPV extension [kUSD]'][data['project_site_name'][item]] \
                = data['npv'][item] / 1000
            capacities_stage['NPV/kW extension [USD/kW]'][data['project_site_name'][item]]\
                = capacities_stage['NPV extension [kUSD]'][data['project_site_name'][item]] / data['demand_peak_kW'][item] * 1000

    for item in data_set_ids.index:
        name = "nesp_" + str(data_set_ids['NESP_ID'][item])
        if name in name_list:
            capacities_stage['Peak demand kW webmap'][name] = data_set_ids['Demand'][item]
            capacities_stage['Customers'][name] = data_set_ids['Customers'][item]
            capacities_stage['PV NESP kWp'][name]          = data_set_ids['PV size(kW)'][item]
            capacities_stage['Storage NESP kWh'][name]     = data_set_ids['Battery capacity (kWh)'][item]
            capacities_stage['Genset NESP kW'][name]       = data_set_ids['Generator capacity (kw)'][item]
            capacities_stage['NPV/HH [USD/HH]'][name] = \
                capacities_stage['NPV [kUSD]'][name] / data_set_ids['Customers'][item] * 1000
            capacities_stage['NPV/HH extension [USD/HH]'][name] = \
                capacities_stage['NPV extension [kUSD]'][name] / data_set_ids['Customers'][item] * 1000


    capacities_stage['PV diff [%]'] = \
        (capacities_stage['PV tool kWp'] - capacities_stage['PV NESP kWp']) / capacities_stage['PV NESP kWp'] * 100
    capacities_stage['Storage diff [%]'] = \
        (capacities_stage['Storage tool kWh'] - capacities_stage['Storage NESP kWh']) / capacities_stage['Storage NESP kWh'] * 100
    capacities_stage['Genset diff [%]'] = \
        (capacities_stage['Genset tool kW'] - capacities_stage['Genset NESP kW']) / capacities_stage['Genset NESP kW'] * 100

    per_stage['PV tool total kWp'][file]        = capacities_stage['PV tool kWp'].sum()
    per_stage['PV NESP total kWp'][file]        = capacities_stage['PV NESP kWp'].sum()
    per_stage['PV diff average [%]'][file]      = capacities_stage['PV diff [%]'].mean()
    per_stage['PV diff min [%]'][file] = capacities_stage['PV diff [%]'].min()
    per_stage['PV diff max [%]'][file] = capacities_stage['PV diff [%]'].max()

    per_stage['Storage tool total kWh'][file]   = capacities_stage['Storage tool kWh'].sum()
    per_stage['Storage NESP total kWh'][file]   = capacities_stage['Storage NESP kWh'].sum()
    per_stage['Storage diff average [%]'][file] = capacities_stage['Storage diff [%]'].mean()
    per_stage['Storage diff min [%]'][file] = capacities_stage['Storage diff [%]'].min()
    per_stage['Storage diff max [%]'][file] = capacities_stage['Storage diff [%]'].max()

    per_stage['Genset tool total kW'][file]     = capacities_stage['Genset tool kW'].sum()
    per_stage['Genset NESP total kW'][file]     = capacities_stage['Genset NESP kW'].sum()
    per_stage['Genset diff average [%]'][file]  = capacities_stage['Genset diff [%]'].mean()
    per_stage['Genset diff min [%]'][file] = capacities_stage['Genset diff [%]'].min()
    per_stage['Genset diff max [%]'][file] = capacities_stage['Genset diff [%]'].max()

    per_stage['RES average [%]'][file] = capacities_stage['RES [%]'].mean()
    per_stage['RES min [%]'][file] = capacities_stage['RES [%]'].min()
    per_stage['RES max [%]'][file] = capacities_stage['RES [%]'].max()

    per_stage['LCOE average [USD/kWh]'][file] = capacities_stage['LCOE [USD/kWh]'].mean()
    per_stage['LCOE min [USD/kWh]'][file] = capacities_stage['LCOE [USD/kWh]'].min()
    per_stage['LCOE max [USD/kWh]'][file] = capacities_stage['LCOE [USD/kWh]'].max()

    per_stage['NPV average [kUSD]'][file] = capacities_stage['NPV [kUSD]'].mean()
    per_stage['NPV min [kUSD]'][file] = capacities_stage['NPV [kUSD]'].min()
    per_stage['NPV max [kUSD]'][file] = capacities_stage['NPV [kUSD]'].max()

    per_stage['NPV/HH average [USD/HH]'][file] = capacities_stage['NPV/HH [USD/HH]'].mean()
    per_stage['NPV/HH min [USD/HH]'][file] = capacities_stage['NPV/HH [USD/HH]'].min()
    per_stage['NPV/HH max [USD/HH]'][file] = capacities_stage['NPV/HH [USD/HH]'].max()

    per_stage['NPV/kW average [USD/kW]'][file] = capacities_stage['NPV/kW [USD/kW]'].mean()
    per_stage['NPV/kW min [USD/kW]'][file] = capacities_stage['NPV/kW [USD/kW]'].min()
    per_stage['NPV/kW max [USD/kW]'][file] = capacities_stage['NPV/kW [USD/kW]'].max()

    per_stage['LCOE extension average [USD/kWh]'][file] = capacities_stage['LCOE extension [USD/kWh]'].mean()
    per_stage['LCOE extension min [USD/kWh]'][file] = capacities_stage['LCOE extension [USD/kWh]'].min()
    per_stage['LCOE extension max [USD/kWh]'][file] = capacities_stage['LCOE extension [USD/kWh]'].max()

    per_stage['NPV extension average [kUSD]'][file] = capacities_stage['NPV extension [kUSD]'].mean()
    per_stage['NPV extension min [kUSD]'][file] = capacities_stage['NPV extension [kUSD]'].min()
    per_stage['NPV extension max [kUSD]'][file] = capacities_stage['NPV extension [kUSD]'].max()

    per_stage['NPV/HH extension average [USD/HH]'][file] = capacities_stage['NPV/HH extension [USD/HH]'].mean()
    per_stage['NPV/HH extension min [USD/HH]'][file] = capacities_stage['NPV/HH extension [USD/HH]'].min()
    per_stage['NPV/HH extension max [USD/HH]'][file] = capacities_stage['NPV/HH extension [USD/HH]'].max()

    per_stage['NPV/kW extension average [USD/kW]'][file] = capacities_stage['NPV/kW extension [USD/kW]'].mean()
    per_stage['NPV/kW extension min [USD/kW]'][file] = capacities_stage['NPV/kW extension [USD/kW]'].min()
    per_stage['NPV/kW extension max [USD/kW]'][file] = capacities_stage['NPV/kW extension [USD/kW]'].max()

    #per_stage[][file] = capacities_stage[].mean()
    #per_stage[][file] = capacities_stage[].min()
    #per_stage[][file] = capacities_stage[].max()


    capacities_stage['Diff NPV/kW [USD/kW]'] = capacities_stage['NPV/kW [USD/kW]'].values - capacities_stage['NPV/kW extension [USD/kW]'].values
    capacities_stage['Diff NPV/HH [USD/HH]'] = capacities_stage['NPV/HH [USD/HH]'].values - capacities_stage['NPV/HH extension [USD/HH]'].values
    capacities_stage['Diff NPV [kUSD]'] = capacities_stage['NPV [kUSD]'].values - capacities_stage['NPV extension [kUSD]'].values
    capacities_stage['Diff LCOE [USD/kWh]'] = capacities_stage['LCOE [USD/kWh]'].values - capacities_stage['LCOE extension [USD/kWh]']

    capacities_stage['Relative diff NPV/kW [USD/kW]'] = \
        capacities_stage['Diff NPV/kW [USD/kW]'].values / capacities_stage['NPV/kW [USD/kW]'].values

    capacities_stage['Relative diff NPV/HH [USD/HH]'] = \
        capacities_stage['Diff NPV/HH [USD/HH]'].values / capacities_stage['NPV/HH [USD/HH]'].values

    capacities_stage['Relative diff NPV [kUSD]'] = \
        capacities_stage['Diff NPV [kUSD]'].values / capacities_stage['NPV [kUSD]'].values

    capacities_stage['Relative diff LCOE [USD/kWh]'] = \
        capacities_stage['Diff LCOE [USD/kWh]'].values / capacities_stage['LCOE [USD/kWh]'].values

    if file == "unreliable_stage1_mgs" or file == "reliable_stage1_mgs":
        stage1 = capacities_stage.copy()
    elif file == "unreliable_stage2_mgs" or file == "reliable_stage2_mgs":
        stage2 = capacities_stage.copy()
    elif file == "unreliable_stage3_mgs" or file == "reliable_stage3_mgs":
        stage3 = capacities_stage.copy()
    elif file == "unreliable_no_mgs" or file == "reliable_no_mgs":
        no_mgs = capacities_stage.copy()

    capacities = capacities.append(capacities_stage)

per_stage.to_csv(folder + "results_nesp_comparison_reliable_stages.csv")
capacities.to_csv(folder + "./results_nesp_comparison_reliable.csv")

list_x = ['Peak demand kW',
          'Customers']
list_y = ['LCOE [USD/kWh]',
          'Genset diff [%]',
          'Storage diff [%]',
          'PV diff [%]',
          'RES [%]',
          'NPV/kW [USD/kW]',
          'NPV/HH [USD/HH]']

list = list_x + list_y
plots=pd.DataFrame([capacities[name].values for name in list], index=list).transpose()
number = 0
for x_value in list_x:
    for y_value in list_y:
        print(x_value, y_value)
        if x_value != y_value:
            number += 1
            plots.plot.scatter(
                x=x_value,
                y=y_value,
                title=y_value + ' dependency on ' + x_value)
            plt.savefig(folder +'graph_' + str(number) + '.png', bbox_inches="tight")

comparison_list_y = ['Relative diff NPV/kW [USD/kW]',
                     'Relative diff NPV/HH [USD/HH]',
                     'Relative diff NPV [kUSD]',
                     'Relative diff LCOE [USD/kWh]']
comparison_list_x = ['Customers']

comparison_list = comparison_list_y + comparison_list_x

#stage1=stage1.transpose()
#stage2=stage2.transpose()
#stage3=stage3.transpose()
#no_mgs=no_mgs.transpose()
#plots2=pd.DataFrame([stage2[name].values for name in list], index=list).transpose()
#plots3=pd.DataFrame([stage3[name].values for name in list], index=list).transpose()
#plots0=pd.DataFrame([no_mgs[name].values for name in list], index=list).transpose()

print(stage1)

for x_value in comparison_list_x:
    for y_value in comparison_list_y:
        print(stage1[x_value])
        print(stage1[y_value])
        fig = stage1.plot.scatter(x=x_value, y=y_value)
        stage2.plot.scatter(x=x_value, y=y_value, ax=fig)
        stage3.plot.scatter(x=x_value, y=y_value, ax=fig)
        #no_mgs.plot.scatter(x=x_value, y=y_value, ax=fig)
        fig.show()