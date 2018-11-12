'''
This script creates all possible experiments of a sensitivity analysis with a list of sensitive parameters
(bound by min, max, step lenght) and a list of constant parameters. All parameters are stored in a large
dictonary, including filenames.
'''

import itertools
import numpy as np


class sensitivity():
    def experiments(sensitivity_bounds, constant_values):
        # create empty dictionary
        dictof_oemparameters = {}

        # fill dictionary with all sensitivity ranges defining the different simulations of the sensitivity analysis
        # ! do not use a key two times, as it will be overwritten by new information
        for keys in sensitivity_bounds:
            if sensitivity_bounds[keys]['min'] == sensitivity_bounds[keys]['max']:
                dictof_oemparameters.update({keys: np.array([sensitivity_bounds[keys]['min']])})
            else:
                dictof_oemparameters.update({keys: np.arange(sensitivity_bounds[keys]['min'],
                                                             sensitivity_bounds[keys]['max'],
                                                             sensitivity_bounds[keys]['step'])})
        # fill dictionary with all constant values defining the different simulations of the sensitivity analysis
        # ! do not use a key two times or in sensitivity_bounds as well, as it will be overwritten by new information
        for keys in constant_values:
            dictof_oemparameters.update({keys: np.array([constant_values[keys]])})

        # create all possible combinations of sensitive parameters
        keys, values = zip(*dictof_oemparameters.items())
        experiments = [dict(zip(keys, v)) for v in itertools.product(*values)]
        print(str(len(experiments)) + ' simulations are necessary to perform the sensitivity analysis.')

        # define file postfix to save simulation
        for i in range(0, len(experiments)):
            filename = 's'
            for keys in experiments[i]:
                filename = filename + '_' + keys + '_' + str(experiments[i][keys])
            filename
            experiments[i].update({'filename': filename})

        return experiments

# constants/values of the sensitivity analysis - influencing the base case OEM
oem = {
    'sensitivity_bounds':
        {
            #'fuel_price':     {'min': 0.5,  'max': 1,     'step': 0.1}
        },
    'constant_values':
        {
            'cost_pv':      300,
            'cost_genset':  400,
            'cost_storage': 170,
            'fuel_price':   1,
            'shortage':     0,
            'wacc':         0.05
        }
    }

# constants/variables of the sensitivity analysis - not influencing the base case OEM

nooem = {
    'sensitivity_bounds':
        {
            #'blackout_duration':     {'min': 2,  'max': 2.5,     'step': 0.5}
        },
    'constant_values':
        {
            'blackout_frequency':   7,
            'blackout_duration':    2,
            'distance_to_grid':     10
        }
    }

oem_experiments=sensitivity.experiments(oem['sensitivity_bounds'], oem['constant_values'])
print (oem_experiments[0])

nooem_experiments=sensitivity.experiments(nooem['sensitivity_bounds'], nooem['constant_values'])
print(nooem_experiments[0])