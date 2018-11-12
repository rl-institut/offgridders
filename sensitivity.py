'''
This script creates all possible experiments of a sensitivity analysis with a list of sensitive parameters
(bound by min, max, step lenght) and a list of constant parameters. All parameters are stored in a large
dictonary, including filenames.
'''

class sensitivity():
    def experiments(sensitivity_bounds, constant_values):
        import itertools
        import numpy as np
        # create empty dictionary
        dictof_oemparameters = {}

        # fill dictionary with all sensitivity ranges defining the different simulations of the sensitivity analysis
        # ! do not use a key two times, as it will be overwritten by new information
        for keys in sensitivity_bounds:
            if sensitivity_bounds[keys]['min'] == sensitivity_bounds[keys]['max']:
                dictof_oemparameters.update({keys: np.array([sensitivity_bounds[keys]['min']])})
            else:
                dictof_oemparameters.update({keys: np.arange(sensitivity_bounds[keys]['min'],
                                                             sensitivity_bounds[keys]['max']+sensitivity_bounds[keys]['step']/2,
                                                             sensitivity_bounds[keys]['step'])})
        # fill dictionary with all constant values defining the different simulations of the sensitivity analysis
        # ! do not use a key two times or in sensitivity_bounds as well, as it will be overwritten by new information
        for keys in constant_values:
            dictof_oemparameters.update({keys: np.array([constant_values[keys]])})

        # create all possible combinations of sensitive parameters
        keys, values = zip(*dictof_oemparameters.items())
        experiments = [dict(zip(keys, v)) for v in itertools.product(*values)]

        # define file postfix to save simulation
        for i in range(0, len(experiments)):
            filename = '_s'
            for keys in sensitivity_bounds:
            #for keys in experiments[i]:
                filename = filename + '_' + keys + '_' + str(round(experiments[i][keys],2))
            if filename == '_s': filename = ''
            experiments[i].update({'filename': filename})

        return experiments


    def blackout_experiments(sensitivity_bounds, constant_values):
        import itertools
        import numpy as np

        dictof_oemparameters = {}
        for keys in sensitivity_bounds:
            if keys == 'blackout_duration' or keys == 'blackout_frequency':
                if sensitivity_bounds[keys]['min'] == sensitivity_bounds[keys]['max']:
                    dictof_oemparameters.update({keys: np.array([sensitivity_bounds[keys]['min']])})
                else:
                    dictof_oemparameters.update({keys: np.arange(sensitivity_bounds[keys]['min'],
                                                                 sensitivity_bounds[keys]['max']+sensitivity_bounds[keys]['step']/2,
                                                                 sensitivity_bounds[keys]['step'])})
        for keys in constant_values:
            if keys == 'blackout_duration' or keys == 'blackout_frequency':
                dictof_oemparameters.update({keys: np.array([constant_values[keys]])})

        # create all possible combinations of sensitive parameters
        keys, values = zip(*dictof_oemparameters.items())
        experiments = [dict(zip(keys, v)) for v in itertools.product(*values)]

        # define file postfix to save simulation
        for i in range(0, len(experiments)):
            filename = 's'
            for keys in experiments[i]:
                filename = filename + '_' + keys + '_' + str(round(experiments[i][keys],2))

            experiments[i].update({'filename': filename})

        return experiments