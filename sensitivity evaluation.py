import pandas as pd
import matplotlib.pyplot as plt
import pprint as pp

data = pd.read_csv('./simulation_results/results.csv', index_col=0)

list_of_cases   =   ['mg_hybrid_no_min', 'mg_hybrid', 'solar_battery_mg', 'diesel_mg']
list_of_locations   =   ['107_Balut Is.', '34_Araceli', '108_Lebak-Kalamansig', '17_Polo', '32_Taytay', '53_Nabuctot', '126_Pangutaran', '20_Mamburao', '105_Cinco-Rama', '121_Tandubanak.csv']
########### Evaluation Time #############

number_of_experiments={}

times_s = {}
for entry in list_of_cases:
    times_s.update({entry: 0})
    number_of_experiments.update({entry: 0})

for line in data.index:
    if data['shortage_max_share'][line]==0:
        times_s.update({data['case'][line]: times_s[data['case'][line]] + data['simulation_time'][line]})
        number_of_experiments.update({data['case'][line]: number_of_experiments[data['case'][line]]+1})

print (number_of_experiments)
times_min = {}
for key in times_s.keys():
    times_min.update({key: times_s[key]/60})

times_hr = {}
for key in times_min.keys():
    times_hr.update({key: times_min[key]/60})

avg_time_min = {}
for key in times_min.keys():
    avg_time_min.update({key: times_min[key]/number_of_experiments[key]})

print('Average simulation time of cases:')
pp.pprint(avg_time_min)

########### LCOE dep. on peak/mean  #############
peak_mean = {
    '126_Pangutaran':4.7,
    '53_Nabuctot':3.9,
    '17_Polo':6,
    '105_Cinco-Rama':3.8,
    '121_Tandubanak.csv':2.9,
    '107_Balut Is.':1.9,
    '108_Lebak-Kalamansig':1.6,
    '34_Araceli':2.2,
    '32_Taytay':1.7,
    '20_Mamburao':1.6}

lcoe = {}
for entry in list_of_cases:
    lcoe.update({entry: 0})

lcoe = pd.DataFrame(index=[key for key in peak_mean.keys()], columns=list_of_cases)
for line in data.index:
    if data['shortage_max_share'][line]==0:
       lcoe[data['case'][line]][data['project_site_name'][line]]=data['lcoe'][line]

lcoe['peak/mean demand']=[peak_mean[key] for key in peak_mean.keys()]
lcoe.to_csv('./simulation_results/lcoe.csv')
lcoe = pd.DataFrame(lcoe.values, columns=lcoe.columns, index=[peak_mean[key] for key in peak_mean.keys()])
lcoe.plot()
plt.show()

res = pd.DataFrame(index=[key for key in peak_mean.keys()], columns=list_of_cases)
for line in data.index:
    if data['shortage_max_share'][line]==0:
       res[data['case'][line]][data['project_site_name'][line]]=data['res_share'][line]

res['peak/mean demand']=[peak_mean[key] for key in peak_mean.keys()]
res.to_csv('./simulation_results/res.csv')
res = pd.DataFrame(res.values, columns=res.columns, index=[peak_mean[key] for key in peak_mean.keys()])

plt.show()
