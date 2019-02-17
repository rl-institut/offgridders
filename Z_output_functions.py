'''
Collect all functions regarding outputs in this file
'''

import pandas as pd
import pprint as pp
import matplotlib

import matplotlib.pyplot as plt
import logging

import oemof.solph as solph
import oemof.graph as graph
import networkx as nx

class output_results:
    def overall_results_title(settings, number_of_project_sites, sensitivity_array_dict):
        logging.debug('Generated header for results.csv')
        title_overall_results = pd.DataFrame(columns=[
            'case',
            'filename'])

        if settings['results_demand_characteristics'] == True:
            title_overall_results = pd.concat([title_overall_results, pd.DataFrame(columns=[
                'total_demand_annual_kWh',
                'demand_peak_kW',
                'total_demand_supplied_annual_kWh',
                'total_demand_shortage_annual_kWh'])], axis=1, sort=False)

        if settings['results_blackout_characteristics'] == True:
            title_overall_results = pd.concat([title_overall_results, pd.DataFrame(columns=[
                'national_grid_reliability_h',
                'national_grid_total_blackout_duration',
                'national_grid_number_of_blackouts'])], axis=1, sort=False)

        title_overall_results = pd.concat([title_overall_results, pd.DataFrame(columns=[
            'capacity_pv_kWp',
            'capacity_wind_kW',
            'capacity_storage_kWh',
            'capacity_genset_kW',
            'capacity_pcoupling_kW',
            'consumption_fuel_annual_l',
            'consumption_main_grid_mg_side_annual_kWh',
            'feedin_main_grid_mg_side_annual_kWh'])], axis=1, sort=False)

        if settings['results_annuities'] == True:
            title_overall_results = pd.concat([title_overall_results, pd.DataFrame(columns=[
                'annuity_pv',
                'annuity_wind',
                'annuity_storage',
                'annuity_genset',
                'annuity_pcoupling',
                'annuity_distribution_grid',
                'annuity_project',
                'annuity_grid_extension'])], axis=1, sort=False)

        title_overall_results = pd.concat([title_overall_results, pd.DataFrame(columns=[
            'expenditures_fuel_annual',
            'expenditures_main_grid_consumption_annual',
            'expenditures_shortage_annual',
            'revenue_main_grid_feedin_annual'])], axis=1, sort=False)

        # Called costs because they include the operation, while they are also not the present value because
        # the variable costs are included in the oem
        if settings['results_costs'] == True:
            title_overall_results = pd.concat([title_overall_results, pd.DataFrame(columns=[
                'costs_pv',
                'costs_wind',
                'costs_storage',
                'costs_genset',
                'costs_pcoupling',
                'costs_distribution_grid',
                'costs_project',
                'costs_grid_extension',
                'expenditures_fuel_total',
                'expenditures_main_grid_consumption_total',
                'expenditures_shortage_total',
                'revenue_main_grid_feedin_total'])], axis=1, sort=False)

        title_overall_results = pd.concat([title_overall_results, pd.DataFrame(columns=[
            'res_share',
            'autonomy_factor',
            'supply_reliability_kWh',
            'annuity',
            'npv',
            'lcoe',
            'objective_value',
            'simulation_time',
            'evaluation_time',
            'comments'])], axis=1, sort=False)

        if number_of_project_sites > 1:
            title_overall_results = pd.concat([title_overall_results, pd.DataFrame(columns=['project_site_name'])], axis=1)

        for keys in sensitivity_array_dict:
            title_overall_results = pd.concat([title_overall_results, pd.DataFrame(columns=[keys])], axis=1)

        return title_overall_results

class output:
    def check_output_directory(experiments):
        logging.debug('Checking for folders and files')
        """ Checking for output folder, creating it if nonexistant and deleting files if needed """
        import os
        for experiment in experiments:
            output_folder = experiments[experiment]['output_folder']
            # First check for or create all necessary sub-folders
            if os.path.isdir(output_folder) != True:
                os.mkdir(output_folder)
            if os.path.isdir(output_folder + '/oemof') != True:
                os.mkdir(output_folder + '/oemof')
            if os.path.isdir(output_folder + '/lp_files') != True:
                os.mkdir(output_folder + '/lp_files')
            if os.path.isdir(output_folder + '/storage') != True:
                os.mkdir(output_folder + '/storage')
            if os.path.isdir(output_folder + '/electricity_mg') != True:
                os.mkdir(output_folder + '/electricity_mg')

            # If oemof results are not to be used, ALL files will be deleted from subfolders
            # This includes lp files, oemof files, csv and png results
            # multiple times due to multiple experiments - possible t save each experimentin seperate folder?!
            if  experiments[experiment]['restore_oemof_if_existant'] == False:
                for root, dirs, files in os.walk(output_folder):
                    for f in files:
                        os.remove(root + '/' + f)
                logging.debug('Deleted all files in folder ' + experiments[experiment]['output_folder'])
        return

    def print_oemof_meta_main_invest(experiment, meta, electricity_bus, case_name):
        if experiment['display_meta'] == True:
            logging.info('********* Meta results *********')
            pp.pprint(meta)

        # print the sums of the flows around the electricity bus
        if experiment['display_main'] == True:
            logging.info('********* Main results *********')
            pp.pprint(electricity_bus['sequences'].sum(axis=0))

        # print the scalars of investment optimization (not equal to capacities!)
        if case_name == "base_oem" or case_name == "base_oem_with_min_loading":
            if experiment['display_invest'] == True:
                logging.info('********* Invest results *********')
                pp.pprint(electricity_bus['scalars'])
        return

    def save_mg_flows(experiment, case_dict, e_flows_df, filename):
        logging.debug('Saving flows MG.')
        flows_connected_to_electricity_mg_bus = [
            'Demand shortage',
            'Demand supplied',
            'PV generation',
            'Wind generation',
            'Excess electricity',
            'Consumption from main grid (MG side)',
            'Feed into main grid (MG side)',
            'Storage discharge',
            'Storage SOC'
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

        if experiment['save_to_csv_flows_storage'] == True:
            mg_flows.to_csv(experiment['output_folder'] + '/electricity_mg/' + case_dict['case_name'] + filename + '_electricity_mg.csv')

        if experiment['save_to_png_flows_electricity_mg'] == True:
            if 'Storage SOC' in mg_flows.columns:
                mg_flows.drop(['Storage SOC'], axis=1)
            fig = mg_flows.plot(title = 'MG Operation of case ' + case_dict['case_name'] + ' in ' + experiment['project_site_name'])
            fig.set(xlabel='Time', ylabel='Electricity flow in kWh')
            fig.legend(loc='upper right')
            plt.savefig(experiment['output_folder'] + '/electricity_mg/' + case_dict['case_name'] + filename + '_electricity_mg.png')
            plt.close()
            plt.clf()
            plt.cla()
            if (len(mg_flows['Demand']) >= 7 * 24):
                fig = mg_flows[0:7 * 24].plot(title = 'MG Operation of case ' + case_dict['case_name'] + ' in ' + experiment['project_site_name'])
                fig.set(xlabel='Time', ylabel='Electricity flow in kWh')
                fig.legend(loc='upper right')
                plt.savefig(experiment['output_folder'] + '/electricity_mg/' + case_dict['case_name'] + filename + '_electricity_mg_7days.png')
                plt.close()
                plt.clf()
                plt.cla()
        return

    def save_storage(experiment, case_dict, e_flows_df, filename):
        logging.debug('Saving flows storage.')
        if case_dict['storage_fixed_capacity'] != None:

            flows_connected_to_electricity_mg_bus = [
                'Storage discharge',
                'Storage charge',
                'Storage SOC']
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

            if experiment['save_to_csv_flows_storage'] == True:
                storage_flows.to_csv(experiment['output_folder'] + '/storage/' + case_dict['case_name'] + filename + '_storage.csv')

            if experiment['save_to_png_flows_storage'] == True:
                fig = storage_flows.plot(title = 'Storage flows of case ' + case_dict['case_name'] + ' in ' + experiment['project_site_name'])
                fig.set(xlabel='Time', ylabel='Electricity flow/stored in kWh')
                fig.legend(loc='upper right')
                plt.savefig(experiment['output_folder'] + '/storage/' + case_dict['case_name'] + filename + '_storage.png')
                plt.close()
                plt.clf()
                plt.cla()
                if (len(storage_flows['Stored capacity']) >= 7*24):
                    fig = storage_flows[0:7*24].plot(title='Storage flows of case ' + case_dict['case_name'] + ' in ' + experiment['project_site_name'])
                    fig.set(xlabel='Time', ylabel='Electricity flow/stored in kWh')
                    fig.legend(loc='upper right')
                    plt.savefig(experiment['output_folder'] + '/storage/' + case_dict['case_name'] + filename + '_storage_7days.png')
                    plt.close()
                    plt.clf()
                    plt.cla()
        return

    def save_double_diagram(experiment, case_dict, e_flows_df, filename):
        flows_connected_to_electricity_mg_bus = [
            'Demand shortage',
            'Demand supplied',
            'PV generation',
            'Wind generation',
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

        if experiment['save_to_csv_flows_storage'] == True:
            mg_flows.to_csv(experiment['output_folder'] + '/electricity_mg/' + case_dict['case_name'] + filename + '_electricity_mg.csv')

        if experiment['save_to_png_flows_electricity_mg'] == True:
            fig = mg_flows.plot(title = 'MG Operation of case ' + case_dict['case_name'] + ' in ' + experiment['project_site_name'])
            fig.set(xlabel='Time', ylabel='Electricity flow in kWh')
            fig.legend(loc='upper right')
            plt.savefig(experiment['output_folder'] + '/electricity_mg/' + case_dict['case_name'] + filename + '_electricity_mg.png')
            plt.close()
            plt.clf()
            plt.cla()
            if (len(mg_flows['Demand']) >= 7 * 24):
                fig = mg_flows[0:7 * 24].plot(title = 'MG Operation of case ' + case_dict['case_name'] + ' in ' + experiment['project_site_name'])
                fig.set(xlabel='Time', ylabel='Electricity flow in kWh')
                fig.legend(loc='upper right')
                plt.savefig(experiment['output_folder'] + '/electricity_mg/' + case_dict['case_name'] + filename + '_electricity_mg_7days.png')
                plt.close()
                plt.clf()
                plt.cla()
        return


    def save_network_graph(energysystem, case_name):
        logging.debug('Generate networkx diagram')
        energysystem_graph = graph.create_nx_graph(energysystem)
        graph_file_name = case_name+'_graph'
        graph_path = './simulation_results/'+graph_file_name
        nx.readwrite.write_gpickle(G=energysystem_graph, path=graph_path)
        energysystem_graph = nx.readwrite.read_gpickle(graph_path)
        matplotlib.rcParams['figure.figsize'] = [20.0, 15.0]

        output.draw_graph(energysystem_graph, case_name, node_size=5500,
                   node_color={
                       'coal': '#0f2e2e',
                       'gas': '#c76c56',
                       'oil': '#494a19',
                       'lignite': '#56201d',
                       'bel': '#9a9da1',
                       'bth': '#cd3333',
                       'wind': '#4ca7c3',
                       'pv': '#ffde32',
                       'demand_el': '#9a9da1',
                       'excess_el': '#9a9da1',
                       'demand_th': '#cd3333',
                       'pp_coal': '#0f2e2e',
                       'pp_lig': '#56201d',
                       'pp_gas': '#c76c56',
                       'pp_oil': '#494a19',
                       'pp_chp': '#eeac7e',
                       'b_heat_source': '#cd3333',
                       'heat_source': '#cd3333',
                       'heat_pump': '#42c77a'},
                   edge_color='#eeac7e')


    def draw_graph(grph, case_name, edge_labels=True, node_color='#AFAFAF',
                   edge_color='#CFCFCF', plot=True, node_size=2000,
                   with_labels=True, arrows=True, layout='neato'):
        """
        Draw a graph. This function will be removed in future versions.

        Parameters
        ----------
        grph : networkxGraph
            A graph to draw.
        edge_labels : boolean
            Use nominal values of flow as edge label
        node_color : dict or string
            Hex color code oder matplotlib color for each node. If string, all
            colors are the same.

        edge_color : string
            Hex color code oder matplotlib color for edge color.

        plot : boolean
            Show matplotlib plot.

        node_size : integer
            Size of nodes.

        with_labels : boolean
            Draw node labels.

        arrows : boolean
            Draw arrows on directed edges. Works only if an optimization_model has
            been passed.
        layout : string
            networkx graph layout, one of: neato, dot, twopi, circo, fdp, sfdp.
        """
        if type(node_color) is dict:
            node_color = [node_color.get(g, '#AFAFAF') for g in grph.nodes()]

        # set drawing options
        options = {
            'prog': 'dot',
            'with_labels': with_labels,
            #'node_color': node_color,
            'edge_color': edge_color,
            'node_size': node_size,
            'arrows': arrows
        }

        # draw graph
        pos = nx.drawing.nx_agraph.graphviz_layout(grph, prog=layout)

        nx.draw(grph, pos=pos, **options)

        # add edge labels for all edges
        if edge_labels is True and plt:
            labels = nx.get_edge_attributes(grph, 'weight')
            nx.draw_networkx_edge_labels(grph, pos=pos, edge_labels=labels)

        # show output
        if plot is True:
            plt.show()

class sarah:
    import pandas as pd
    import matplotlib.pyplot as plt

    def shape_legend(node, reverse=False, **kwargs):
        handels = kwargs['handles']
        labels = kwargs['labels']
        axes = kwargs['ax']
        parameter = {}

        new_labels = []
        for label in labels:
            label = label.replace('(', '')
            label = label.replace('), flow)', '')
            label = label.replace(node, '')
            label = label.replace(',', '')
            label = label.replace(' ', '')
            new_labels.append(label)
        labels = new_labels

        parameter['bbox_to_anchor'] = kwargs.get('bbox_to_anchor', (1, 0.5))
        parameter['loc'] = kwargs.get('loc', 'center left')
        parameter['ncol'] = kwargs.get('ncol', 1)
        plotshare = kwargs.get('plotshare', 0.9)

        if reverse:
            handels = handels.reverse()
            labels = labels.reverse()

        box = axes.get_position()
        axes.set_position([box.x0, box.y0, box.width * plotshare, box.height])

        parameter['handles'] = handels
        parameter['labels'] = labels
        axes.legend(**parameter)
        return axes

    def plotfcn(filepath):

        fig, ax = plt.subplots(2, 1, sharex=True, figsize=(16 / 2.54, 10 / 2.54))
        plt.rc('legend', **{'fontsize': 10})
        plt.rcParams.update({'font.size': 10})
        # plt.rc('text', usetex=True)
        # plt.rcParams.update({'text.usetex':True})

        params = {'font.size': 11,
                  'font.family': 'serif',
                  'font.serif': 'cmr10'}
        plt.rcParams.update(params)
        fig.subplots_adjust(left=0.1, bottom=0.12, right=0.86, top=0.93,
                            wspace=0.03, hspace=0.2)

        # read in plotdata as pd.DataFrame

        df = pd.read_csv(filepath)

        # set index to pd.DatetimeIndex from colum['timestamp']

        df.set_index(pd.DatetimeIndex(df['timestamp'], freq='H'), drop=True, inplace=True)

        # slice df to sequence that should be plotted

        df_slice = df.iloc[4334:4430]

        col = list(df_slice)

        # subplot 1
        order = [1, 2, 3, 5, 7, 10, 13, 15]

        neworder = [col[x] for x in order]

        df_no = df_slice[neworder]

        df_no = df_no.rename(columns={"(('electricity', 'demand'), 'flow')": 'load',
                                      "(('PV', 'electricity_dc'), 'flow')": 'PV',
                                      "(('electricity_dc', 'storage'), 'flow')": 'BSS_{in}',
                                      "(('storage', 'electricity_dc'), 'flow')": 'BSS_{out}',
                                      "(('pp_oil_1', 'electricity'), 'flow')": 'DG1',
                                      "(('pp_oil_2', 'electricity'), 'flow')": 'DG2',
                                      "(('pp_oil_3', 'electricity'), 'flow')": 'DG3',
                                      "(('electricity', 'excess'), 'flow')": 'excess'})

        cdict1 = {
            'load': '#ce27d1',
            'PV': '#ffde32',
            'BSS_{in}': '#42c77a',
            'DG2': '#636f6b',
            'DG1': '#435cb2',
            'DG3': '#20b4b6',
            'BSS_{out}': '#42c77a',
            'excess': '#5b5bae'
        }

        in_flow = ['PV', 'BSS_{out}', 'DG1', 'DG2', 'DG3']
        out_flow = ['load', 'BSS_{in}', 'excess']
        df_in = df_no.loc[:, in_flow]
        myplot = oev.io_plot(df_in=df_no.loc[:, in_flow], df_out=df_no.loc[:, out_flow],
                             inorder=['PV', 'BSS_{out}', 'DG1', 'DG2', 'DG3'], outorder=['load', 'BSS_{in}', 'excess'],
                             cdict=cdict1, ax=ax[0], line_kwa={'linewidth': 1})
        # ax[0] = shape_legend('electricity', **myplot)
        # oev.set_datetime_ticks(ax[0], df.index[4344:4440], tick_distance=24,
        # date_format='%d-%m %H ', offset=10)
        myplot['ax'].set_ylabel('Power / kW')
        myplot['ax'].set_xlabel('')
        # myplot['ax'].set_xticklabels('')

        myplot['ax'].get_xaxis().set_visible(False)
        # myplot['ax'].set_xlim(0, x_length)
        # myplot['ax'].set_title("Electric power output")
        myplot['ax'].legend_.remove()

        # subplot 2
        df_soc = df_slice.loc[:, "(('storage', 'None'), 'capacity')"]
        df_soc.rename(columns={"(('storage', 'None'), 'capacity')": 'SOC_{BSS}'})
        df_soc = df_soc / df_soc.max()

        df_soc.reset_index(drop=True, inplace=True)

        ax1 = df_soc.plot(kind='line', linewidth=1, color='r', ax=ax[1], legend=True, drawstyle='steps-mid')
        oev.set_datetime_ticks(ax1, df.index[4344:4440], tick_distance=24,
                               date_format='%d-%m %H ', offset=10)
        ax1.set_ylabel('State of Charge $SOC$ ')
        ax1.set_xlabel('Datetime / DD-MM hh')
        ax1.set_ylim(0.5, 1.005, 0.1)
        ax1.grid(True, linestyle='--')
        # myplot['ax'].get_xaxis().set_visible(False)
        # myplot['ax'].set_xlim(0, x_length)
        ax1.legend_.remove()

        parameters = {}

        handles, labels = ax1.get_legend_handles_labels()

        parameters['handles'] = myplot['handles']
        parameters['handles'] += handles

        parameters['labels'] = myplot['labels']
        parameters['labels'] += ['SOC_{BSS}']

        box = ax[0].get_position()
        ax[0].set_position([box.x0, box.y0, box.width * 0.9, box.height])

        box1 = ax[1].get_position()
        ax[1].set_position([box1.x0, box1.y0, box1.width * 0.9, box1.height])

        fig.legend(parameters['handles'], parameters['labels'], 'center right', bbox_to_anchor=(1, 0.5))

        plt.show()

        # ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])

        # Put a legend to the right of the current axis
        # ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))

    if __name__ == '__main__':
        plotfcn('data/diesel_pv_batt_sim_P1_B1_2_8760.csv')
