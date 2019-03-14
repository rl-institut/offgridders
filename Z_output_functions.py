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
        import shutil
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
            # delete folder inputs
            if os.path.isdir(output_folder + '/inputs') == True:
                shutil.rmtree(output_folder + '/inputs')
                shutil.copytree('./inputs', './' + output_folder + '/inputs')

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
            'Demand'
            'Demand shortage',
            'Demand supplied',
            'PV generation',
            'Wind generation',
            'Excess electricity',
            'Consumption from main grid (MG side)',
            'Feed into main grid (MG side)',
            'Storage discharge',
            'Storage SOC',
            'Storage charge',
            'Genset generation',
            'Grid availability',
            'Excess generation']
        mg_flows = pd.DataFrame(e_flows_df['Demand'].values, columns=['Demand'], index=e_flows_df['Demand'].index)
        for entry in flows_connected_to_electricity_mg_bus:
            if entry in e_flows_df.columns:
                if entry in ['Storage discharge', 'Demand shortage', 'Feed into main grid (MG side)']:
                    # Display those values as negative in graphs/files
                    if entry == 'Feed into main grid (MG side)':
                        new_column = pd.DataFrame(-e_flows_df[entry].values,
                                                  columns=['Feed into main grid'],
                                                  index=e_flows_df[entry].index)
                    else:
                        new_column = pd.DataFrame(-e_flows_df[entry].values, columns=[entry], index=e_flows_df[entry].index) # Display those values as negative in graphs/files
                elif entry == 'Consumption from main grid (MG side)':
                    new_column = pd.DataFrame(e_flows_df[entry].values,
                                              columns=['Consumption from main grid'],
                                              index=e_flows_df[entry].index)
                elif (entry == 'Demand supplied' or entry == 'Demand shortage') and (e_flows_df['Demand'].values==e_flows_df['Demand supplied'].values):
                    pass

                else:
                    new_column = pd.DataFrame(e_flows_df[entry].values, columns=[entry], index=e_flows_df[entry].index)

                mg_flows = mg_flows.join(new_column)

        if experiment['save_to_csv_flows_electricity_mg'] == True:
            mg_flows.to_csv(experiment['output_folder'] + '/electricity_mg/' + case_dict['case_name'] + filename + '_electricity_mg.csv')

        if experiment['save_to_png_flows_electricity_mg'] == True:
            number_of_subplots = 0

            if 'Storage SOC' in mg_flows.columns:
                mg_flows = mg_flows.drop(['Storage SOC'], axis=1)
                if case_dict['storage_fixed_capacity'] != None:
                    number_of_subplots += 1
            if 'Grid availability' in mg_flows.columns:
                mg_flows = mg_flows.drop(['Grid availability'], axis=1)
                if (case_dict['pcc_consumption_fixed_capacity'] != None) or (case_dict['pcc_feedin_fixed_capacity'] != None):
                    number_of_subplots += 1

            for timeframe in ['year', 'days']:
                if timeframe == 'year':
                    output.plot_flows(case_dict, experiment, mg_flows, e_flows_df, number_of_subplots)
                    plt.savefig(experiment['output_folder'] + '/electricity_mg/' + case_dict[
                        'case_name'] + filename + '_electricity_mg.png', bbox_inches="tight")

                elif timeframe == 'days' and (len(mg_flows['Demand']) >= 5 * 24):
                    output.plot_flows(case_dict, experiment, mg_flows[0:5 * 24], e_flows_df[0:5 * 24], number_of_subplots)
                    plt.savefig(experiment['output_folder'] + '/electricity_mg/' + case_dict[
                        'case_name'] + filename + '_electricity_mg_5days.png', bbox_inches="tight")

                plt.close()
                plt.clf()
                plt.cla()

        return

    def plot_flows(case_dict, experiment, mg_flows, e_flows_df, number_of_subplots):
        if number_of_subplots < 1:
            fig, axes = plt.subplots(nrows=1, figsize=(16 / 2.54, 10 / 2.54 / 2))
            axes_mg = axes
        else:
            fig, axes = plt.subplots(nrows=2, figsize=(16 / 2.54, 10 / 2.54))
            axes_mg = axes[0]

        color_dict = {
            'Demand': '#ccccff', # pidgeon blue
            'Demand supplied': '#0033cc', # blue
            'PV generation': '#ffcc00', # orange
            'Wind generation': '#33ccff', # light blue
            'Genset generation': '#000000', # black
            'Consumption from main grid': '#990099', # violet
            'Storage charge': '#33ff00', # light green
            'Excess generation': '#996600', # brown
            'Feed into main grid': '#ff33cc', # pink
            'Storage discharge': '#33ff00', # dark green
            'Demand shortage': '#ff3300',  # bright red
            'Storage SOC': '#66cc33', # grass green
            'Grid availability': '#cc0000' # red
        }

        mg_flows.plot(title='MG Operation of case ' + case_dict['case_name'] + ' in ' + experiment['project_site_name'],
                      color=[color_dict.get(x, '#333333') for x in mg_flows.columns],
                      ax=axes_mg,
                      drawstyle='steps-mid')
        axes_mg.set(xlabel='Time', ylabel='Electricity flow in kWh')
        axes_mg.legend(loc='center left', bbox_to_anchor=(1, 0.5), frameon=False)

        if number_of_subplots >= 1:
            ylabel = ''
            if ((case_dict['pcc_consumption_fixed_capacity'] != None) or (case_dict['pcc_feedin_fixed_capacity'] != None)) \
                    and ('Grid availability' in e_flows_df.columns):
                e_flows_df['Grid availability'].plot(ax=axes[1],
                                                     color=[color_dict.get(x, '#333333') for x in mg_flows.columns],
                                                     drawstyle='steps-mid')
                ylabel += 'Grid availability'

            if number_of_subplots > 1:
                ylabel += ',\n '

            if (case_dict['storage_fixed_capacity'] != None) \
                    and ('Storage SOC' in e_flows_df.columns):
                e_flows_df['Storage SOC'].plot(ax=axes[1],
                                               color=[color_dict.get(x, '#333333') for x in mg_flows.columns],
                                               drawstyle='steps-mid')
                ylabel += 'Storage SOC'

            axes[1].set(xlabel='Time', ylabel=ylabel)
            if number_of_subplots > 1:
                axes[1].legend(loc='center left', bbox_to_anchor=(1, 0.5), frameon=False)

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
                fig.legend(loc='center left', bbox_to_anchor=(1, 0.5), frameon=False)
                plt.savefig(experiment['output_folder'] + '/storage/' + case_dict['case_name'] + filename + '_storage.png', bbox_inches="tight")
                plt.close()
                plt.clf()
                plt.cla()
                if (len(storage_flows['Stored capacity']) >= 5*24):
                    fig = storage_flows[0:5*24].plot(title='Storage flows of case ' + case_dict['case_name'] + ' in ' + experiment['project_site_name'])
                    fig.set(xlabel='Time', ylabel='Electricity flow/stored in kWh')
                    fig.legend(loc='center left', bbox_to_anchor=(1, 0.5), frameon=False)
                    plt.savefig(experiment['output_folder'] + '/storage/' + case_dict['case_name'] + filename + '_storage_7days.png', bbox_inches="tight")
                    plt.close()
                    plt.clf()
                    plt.cla()
        return
    '''
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
        
        return

'''