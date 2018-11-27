'''
This script creates all possible experiments of a sensitivity analysis with a list of sensitive parameters
(bound by min, max, step lenght) and a list of constant parameters. All parameters are stored in a large
dictonary, including filenames.
'''

import pprint as pp
import pandas as pd

class sensitivity():
    def experiments():
        from input_values import input_files_demand, sensitivity_bounds, sensitivity_constants
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
        for keys in sensitivity_constants:
            dictof_oemparameters.update({keys: np.array([sensitivity_constants[keys]])})

        demand_array = []
        for files in input_files_demand:
            demand_array.append(files)

        dictof_oemparameters.update({'demand_profile': demand_array})

        # create all possible combinations of sensitive parameters
        keys, values = zip(*dictof_oemparameters.items())
        experiments = [dict(zip(keys, v)) for v in itertools.product(*values)]

        # define file postfix to save simulation
        for i in range(0, len(experiments)):
            filename = '_s'
            if len(demand_array) > 1:
                filename = filename + '_' + experiments[i]['demand_profile']
            else:
                filename = filename
            for keys in sensitivity_bounds:
            #for keys in experiments[i]:
                filename = filename + '_' + keys + '_' + str(round(experiments[i][keys],2))
            if filename == '_s':
                filename = ''
            experiments[i].update({'filename': filename})

        # define structure of pd.Dataframe: overall_results
        overall_results = pd.DataFrame(
            columns=['Case', 'Filename', 'Capacity PV kWp', 'Capacity storage kWh', 'Capacity genset kW', 'Renewable Factor', 'NPV', 'LCOE', 'Annuity', 'Fuel consumption', 'fuel_annual_expenditures', 'Simulation time', 'demand_annual_kWh', 'demand_peak_kW', 'demand_annual_supplied_kWh'])
        if len(demand_array) > 1:
            overall_results = pd.concat([overall_results, pd.DataFrame(columns=['demand_profile'])], axis=1)
        for keys in sensitivity_bounds:
            overall_results = pd.concat([overall_results, pd.DataFrame(columns=[keys])], axis=1)
        return experiments, overall_results

    def blackout_experiments():
        from input_values import sensitivity_bounds, sensitivity_constants
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
        for keys in sensitivity_constants:
            if keys == 'blackout_duration' or keys == 'blackout_frequency':
                dictof_oemparameters.update({keys: np.array([sensitivity_constants[keys]])})

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