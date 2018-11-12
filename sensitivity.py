'''
This script creates all possible experiments of a sensitivity analysis with a list of sensitive parameters
(bound by min, max, step lenght) and a list of constant parameters. All parameters are stored in a large
dictonary, including filenames.
'''

import itertools
import numpy as np

# values of the sensitivity analysis that are variable
sensitivity_bounds={
    'fuel_price':     {'min': 0.5,  'max': 1,     'step': 0.1},
    'shortage':       {'min': 0.5,  'max': 1,     'step': 0.1}
    }

# Values of the sensitivity analysis that appear constant
constant_values = {
    'cost_pv': 300,
    'cost_genset': 400,
    'cost_storage': 170,
    'wacc':           0.05
    }

#dictof_nooemparameters ={'blackout_duration_100':      {min: 2,  max: 4,     step: 0.5},
#                       'blackout_frequency_100':       {min: 10,  max: 10,   step: 1},
#                       'distance_to_grid':             {min: 10,  max: 10,   step: 10}}

dictof_oemparameters = {}

for keys in sensitivity_bounds:
    print(keys)
    if sensitivity_bounds[keys]['min'] == sensitivity_bounds[keys]['max']:
        dictof_oemparameters.update({keys: np.array([sensitivity_bounds[keys]['min']])})
    else:
        dictof_oemparameters.update({keys: np.arange(sensitivity_bounds[keys]['min'],
                                                     sensitivity_bounds[keys]['max'],
                                                     sensitivity_bounds[keys]['step'])})

for keys in constant_values:
    print(keys)
    dictof_oemparameters.update({keys: np.array([constant_values[keys]])})

print (dictof_oemparameters)
keys, values = zip(*dictof_oemparameters.items())
experiments = [dict(zip(keys, v)) for v in itertools.product(*values)]
# number of simulations:
print(str(len(experiments))+ ' simulations are necessary to perform the sensitivity analysis')


for i in range(0, len(experiments)):
    filename = 's'
    for keys in experiments[i]:
        filename = filename + '_' + keys+'_'+str(experiments[i][keys])
    filename
    experiments[i].update({'filename': filename})

print (experiments[0])
