import pandas as pd
import pprint as pp

data = pd.read_csv('./simulation_results/results.csv', index_col=0)
print(data.columns)

list_of_cases   =   ['mg_hybrid_no_min', 'mg_hybrid', 'solar_battery_mg', 'diesel_mg']
list_of_locations   =   ['107_Balut Is.', '34_Araceli', '108_Lebak-Kalamansig', '17_Polo', '32_Taytay', '53_Nabuctot', '126_Pangutaran', '20_Mamburao', '105_Cinco-Rama', '121_Tandubanak.csv']
########### Evaluation Time #############
times_s = {'solarhybrid_backup': 0,
         'solarhybrid_usage_no_min_load': 0,
         'solarhybrid_usage': 0,
         'diesel': 0}
print(data['case'])
for line in data.index:
    #if data['shortage_max_share'][line]==0:
    times_s.update({data['case'][line]: times_s[data['case'][line]] + data['evaluation_time'][line]})
times_min = {}
for key in times_s.keys():
    times_min.update({key: times_s[key]/60})
times_hr = {}
for key in times_min.keys():
    times_hr.update({key: times_min[key]/60})

pp.pprint(times_hr)
print(times_min)
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

lcoe = {'solarhybrid_backup': 0,
         'solarhybrid_usage_no_min_load': 0,
         'solarhybrid_usage': 0,
         'diesel': 0}

lcoe = pd.DataFrame(index=[key for key in peak_mean.keys()], columns=list_of_cases)
for line in data.index:
    #if data['shortage_max_share'][line]==0:
    lcoe[data['case'][line]][data['project_site_name'][line]]=data['lcoe'][line]

lcoe['peak/mean demand']=[peak_mean[key] for key in peak_mean.keys()]
lcoe.to_csv('./simulation_results/lcoe.csv')
lcoe = pd.DataFrame(lcoe.values, columns=lcoe.columns, index=[peak_mean[key] for key in peak_mean.keys()])

res = pd.DataFrame(index=[key for key in peak_mean.keys()], columns=list_of_cases)
for line in data.index:
    #if data['shortage_max_share'][line]==0:
    res[data['case'][line]][data['project_site_name'][line]]=data['res_share'][line]

res['peak/mean demand']=[peak_mean[key] for key in peak_mean.keys()]
res.to_csv('./simulation_results/res.csv')
res = pd.DataFrame(res.values, columns=res.columns, index=[peak_mean[key] for key in peak_mean.keys()])
