'''
Collect all functions regarding outputs in this file
'''

import pandas as pd
import matplotlib.pyplot as plt
class output:
    def print_oemof_meta_main_invest(meta, electricity_bus, case_name):
        from config import print_simulation_meta, print_simulation_main, print_simulation_invest

        if print_simulation_meta == True:
            logging.info('********* Meta results *********')
            pp.pprint(meta)

        # print the sums of the flows around the electricity bus
        if print_simulation_main == True:
            logging.info('********* Main results *********')
            pp.pprint(electricity_bus['sequences'].sum(axis=0))

        # print the scalars of investment optimization (not equal to capacities!)
        if case_name == "base_oem" or case_name == "base_oem_with_min_loading":
            if print_simulation_invest == True:
                logging.info('********* Invest results *********')
                pp.pprint(electricity_bus['scalars'])
        return

    def outputs_mg_flows(case_dict, e_flows_df, filename):
        from config import display_graphs_flows_electricity_mg, setting_save_flows_storage
        flows_connected_to_electricity_mg_bus = [
            'Demand shortage',
            'Demand supplied',
            'PV generation',
            'Excess electricity',
            'Consumption from main grid (MG side)',
            'Feed into main grid (MG side)',
            'Storage discharge',
            'Storage charge',
            'Genset generation',
            'Excess generation']
        mg_flows = pd.DataFrame(e_flows_df['Demand'].values, columns=['Demand'], index=e_flows_df['Demand'].index)
        for entry in flows_connected_to_electricity_mg_bus:
            if entry in e_flows_df.columns:
                if entry in ['Storage discharge', 'Demand shortage', 'Feed into main grid (MG side)']:
                    new_column = pd.DataFrame(-e_flows_df[entry].values, columns=[entry], index=e_flows_df[entry].index) # Display those values as negative in graphs/files
                else:
                    new_column = pd.DataFrame(e_flows_df[entry].values, columns=[entry], index=e_flows_df[entry].index)
                mg_flows = mg_flows.join(new_column)

        if setting_save_flows_storage == True:
            from config import output_folder
            mg_flows.to_csv(output_folder + '/electricity_mg/' + case_dict['case_name'] + filename + '_electricity_mg.csv')

        if display_graphs_flows_electricity_mg == True:
            fig = mg_flows.plot(title = 'MG Operation of case ' + case_dict['case_name'])
            fig.set(xlabel='Time', ylabel='Electricity flow in kWh')
            fig.legend(loc='upper right')
            plt.savefig(output_folder + '/electricity_mg/' + case_dict['case_name'] + filename + '_electricity_mg.png')
            plt.clf()
            # todo change if 15-min intervals
            if (len(mg_flows['Demand']) >= 7 * 24):
                fig = mg_flows[0:7 * 24].plot(title = 'MG Operation of case ' + case_dict['case_name'])
                fig.set(xlabel='Time', ylabel='Electricity flow in kWh')
                fig.legend(loc='upper right')
                plt.savefig(output_folder + '/electricity_mg/' + case_dict['case_name'] + filename + '_electricity_mg_7days.png')
                plt.close()
        return

    def outputs_storage(case_dict, e_flows_df, filename):
        if case_dict['storage_fixed_capacity'] != None:
            from config import display_graphs_flows_storage, setting_save_flows_storage

            flows_connected_to_electricity_mg_bus = [
                'Storage discharge',
                'Storage charge']
            storage_flows = pd.DataFrame(e_flows_df['Stored capacity'].values,
                                    columns=['Stored capacity'],
                                    index=e_flows_df['Stored capacity'].index)

            for entry in flows_connected_to_electricity_mg_bus:
                if entry in e_flows_df.columns:
                    if entry == 'Storage discharge':
                        new_column = pd.DataFrame(-e_flows_df[entry].values, columns=[entry], index=e_flows_df[entry].index)
                    else:
                        new_column = pd.DataFrame(e_flows_df[entry].values, columns=[entry], index=e_flows_df[entry].index)
                    storage_flows = storage_flows.join(new_column)

            if setting_save_flows_storage == True:
                from config import output_folder
                storage_flows.to_csv(output_folder + '/storage/' + case_dict['case_name'] + filename + '_storage.csv')

            if display_graphs_flows_storage == True:
                fig = storage_flows.plot(title = 'Storage flows of case ' + case_dict['case_name'])
                fig.set(xlabel='Time', ylabel='Electricity flow/stored in kWh')
                fig.legend(loc='upper right')
                plt.savefig(output_folder + '/storage/' + case_dict['case_name'] + filename + '_storage.png')
                plt.clf()
                #todo change if 15-min intervals
                if (len(storage_flows['Stored capacity']) >= 7*24):
                    fig = storage_flows[0:7*24].plot(title='Storage flows of case ' + case_dict['case_name'])
                    fig.set(xlabel='Time', ylabel='Electricity flow/stored in kWh')
                    fig.legend(loc='upper right')
                    plt.savefig(output_folder + '/storage/' + case_dict['case_name'] + filename + '_storage_7days.png')
                    plt.close()
        return

    #todo not working
    def draw(energysystem):
        '''
        Compare with https://oemof.readthedocs.io/en/stable/api/oemof.html?highlight=graph#module-oemof.graph for additional settings
        '''
        import oemof.graph as graph
        import networkx as nx
        import matplotlib.pyplot as plt
        from config import output_folder

        energysystem_graph = graph.create_nx_graph(energysystem, filename=output_folder+'/'+'case_graph')

        return