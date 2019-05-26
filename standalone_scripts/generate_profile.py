import pandas as pd
import matplotlib.pyplot as plt

folder = '../inputs/timeseries/'
files = ['nesp_4189.csv',
         'nesp_3573.csv',
         'nesp_3516.csv']

title = ['Demand profile of cluster nesp_4189',
         'Demand profile of cluster nesp_3573',
         'Demand profile of cluster nesp_3516']

for item in range(0, len(files)):
    data = pd.read_csv(folder + files[item], sep=';')
    fig = data['Demand'][0:3*24].plot(drawstyle='steps-mid')
    fig.set(xlabel='Time', ylabel='Demand in kW')

plt.savefig('graph_' + files[item][:-4] + '.png', bbox_inches="tight")