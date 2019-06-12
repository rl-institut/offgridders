import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import seaborn as sns

list = ['../simulation_results/evaluation_1/costs_all_solutions',
        '../simulation_results/evaluation_2/costs_all_solutions',
        '../simulation_results/evaluation_3/costs_all_solutions',
        '../simulation_results/evaluation_4/costs_all_solutions',
        '../simulation_results/evaluation_5/costs_all_solutions',
        '../simulation_results/evaluation_6/costs_all_solutions',
        '../simulation_results/evaluation_7/costs_all_solutions',
        '../simulation_results/evaluation_8/costs_all_solutions',
        '../simulation_results/evaluation_9/costs_all_solutions',
        '../simulation_results/evaluation_10/costs_all_solutions',
        '../simulation_results/evaluation_11/costs_all_solutions',
        '../simulation_results/evaluation_12/costs_all_solutions',
        '../simulation_results/evaluation_13/costs_all_solutions',
        '../simulation_results/evaluation_14/costs_all_solutions',
        '../simulation_results/evaluation_15/costs_all_solutions',
        '../simulation_results/evaluation_16/costs_all_solutions',
        '../simulation_results/evaluation_17/costs_all_solutions',
        '../simulation_results/evaluation_18/costs_all_solutions',
        '../simulation_results/evaluation_19/costs_all_solutions']

header1 = ['LCOE USD per kWh offgrid_mg ',	'LCOE USD per kWh sole_maingrid ',	'LCOE USD per kWh offgrid_mg_cons ',	'LCOE USD per kWh offgrid_mg_cons_prod ',	'LCOE USD per kWh ongrid_mg_cons ',	'LCOE USD per kWh ongrid_mg_cons_prod ',	'LCOE USD per kWh reimbursement ',	'LCOE USD per kWh abandonment ',	'LCOE USD per kWh spp ',	'LCOE USD per kWh spd ',
]
header2 = ['NPV per kW USD per kW offgrid_mg ',
           'NPV per kW USD per kW sole_maingrid ',
           'NPV per kW USD per kW offgrid_mg_cons ',
           'NPV per kW USD per kW offgrid_mg_cons_prod ',
           'NPV per kW USD per kW ongrid_mg_cons ',
           'NPV per kW USD per kW ongrid_mg_cons_prod ',
           'NPV per kW USD per kW reimbursement ',
           'NPV per kW USD per kW abandonment ',
           'NPV per kW USD per kW spp ',
           'NPV per kW USD per kW spd ',
]

header = header1 + header2
color_list = sns.color_palette("colorblind", 10)
color_dict = {'LCOE USD per kWh offgrid_mg': color_list[0],
              'LCOE USD per kWh sole_maingrid': color_list[1],
              'LCOE USD per kWh offgrid_mg_cons': color_list[2],
              'LCOE USD per kWh offgrid_mg_cons_prod': color_list[3],
              'LCOE USD per kWh ongrid_mg_cons': color_list[4],
              'LCOE USD per kWh ongrid_mg_cons_prod': color_list[5],
              'LCOE USD per kWh reimbursement':color_list[6],
              'LCOE USD per kWh spp': color_list[7],
              'LCOE USD per kWh spd': color_list[8],
              'LCOE USD per kWh abandonment':color_list[9],
              'NPV per kW USD per kW offgrid_mg': color_list[0],
              'NPV per kW USD per kW sole_maingrid': color_list[1],
              'NPV per kW USD per kW offgrid_mg_cons': color_list[2],
              'NPV per kW USD per kW offgrid_mg_cons_prod': color_list[3],
              'NPV per kW USD per kW ongrid_mg_cons': color_list[4],
              'NPV per kW USD per kW ongrid_mg_cons_prod': color_list[5],
              'NPV per kW USD per kW reimbursement': color_list[6],
              'NPV per kW USD per kW spp': color_list[7],
              'NPV per kW USD per kW spd': color_list[8],
              'NPV per kW USD per kW abandonment': color_list[9]
              }

for case in color_dict.copy():
    color_dict.update({case+' mg perspective': color_dict[case]})
    color_dict.update({case + ' global perspective': color_dict[case]})

average_5 = pd.DataFrame(index=header)
for perspective in ['mg perspective', 'global perspective']:
    for item in ['_unreliable.csv', '_reliable.csv']:
        costs_trends = pd.DataFrame(index=header)
        year = 1
        for file in list:
            data = pd.read_csv(file+item, index_col=False)
            costs_trends[year] = data[[title + perspective for title in header]].iloc[544].tolist()#, index=header, columns=[year]))
            year += 1
            if file == list[4]:
                average_5[perspective+item]=data[[title + perspective for title in header]].iloc[544].tolist()
                print(data[[title + perspective for title in header]].iloc[544])
        costs_trends = costs_trends.transpose()
        costs_trends['year'] = [i for i in range(1, 20)]
        plotting = 0
        for y in header1:
            if plotting == 0:
                fig = costs_trends.plot(x='year', y=y, label=y[17:], color=color_dict[y+perspective]) # s=df['c'] * 200 plot THREE VALUES
                plotting = 1
            else:
                costs_trends.plot(x='year', y=y, ax=fig, label=y[17:], color=color_dict[y+perspective])
        fig.set(xlabel='year of grid arrival',
                ylabel='LCOE (USD per kWh)',
                title='Dependency on grid arrival '+ perspective)
        plt.legend(loc='center left', bbox_to_anchor=(1, 0.5), frameon=False)
        plt.savefig('../simulation_results/grid_arrival_lcoe_'+perspective+item[:-4]+'.png', bbox_inches="tight")
        plt.close()

        plotting = 0
        for y in header2:
            if plotting == 0:
                fig = costs_trends.plot(x='year', y=y, label=y[22:], color=color_dict[y+perspective]) # s=df['c'] * 200 plot THREE VALUES
                plotting = 1
            else:
                costs_trends.plot(x='year', y=y, ax=fig, label=y[22:], color=color_dict[y+perspective])
        fig.set(xlabel='year of grid arrival',
                ylabel='NPV per kW (USD per kW)',
                title='Dependency on grid arrival '+ perspective)
        plt.legend(loc='center left', bbox_to_anchor=(1, 0.5), frameon=False)
        plt.savefig('../simulation_results/grid_arrival_npv_'+perspective+item[:-4]+'.png', bbox_inches="tight")
        plt.close()
        costs_trends.to_csv('../simulation_results/trends_'+perspective+item+'.csv')
        '''
        costs_5 = pd.read_csv(list[4]+item, nrows=544)
        list_cases = [head[17:] for head in header1]
        to_plot=pd.DataFrame(index=costs_5.index)
        for case in range(0,len(list_cases)):
            to_plot[list_cases[case]]=costs_5[header1[case]+perspective]
        #to_plot = pd.DataFrame(costs_5[[title + perspective for title in header1]], columns=list_cases)
        print(to_plot)
        fig = to_plot.boxplot(column=list_cases, rot=45)
        plt.show()
        plt.savefig('../simulation_results/graph_boxplot_npv_' + perspective + item + '.png',
                    bbox_inches="tight")
        plt.close()
        '''

average_5.to_csv('../simulation_results/average_intercon.csv')
