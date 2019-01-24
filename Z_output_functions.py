'''
Collect all functions regarding outputs in this file
'''

import pandas as pd
import matplotlib.pyplot as plt
import logging

class output_results:
    def overall_results_title(settings, number_of_project_sites, sensitivity_array_dict):
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
                'national_grid_reliability',
                'national_grid_total_blackout_duration',
                'national_grid_number_of_blackouts'])], axis=1, sort=False)

        title_overall_results = pd.concat([title_overall_results, pd.DataFrame(columns=[
            'capacity_pv_kWp',
            'capacity_storage_kWh',
            'capacity_genset_kW',
            'capacity_pcoupling_kW',
            'res_share',
            'consumption_fuel_annual_l',
            'consumption_main_grid_mg_side_annual_kWh',
            'feedin_main_grid_mg_side_annual_kWh'])], axis=1, sort=False)

        if settings['results_annuities'] == True:
            title_overall_results = pd.concat([title_overall_results, pd.DataFrame(columns=[
                'annuity_pv',
                'annuity_storage',
                'annuity_genset',
                'annuity_pcoupling',
                'annuity_distribution_grid',
                'annuity_project',
                'annuity_grid_extension'])], axis=1, sort=False)

        title_overall_results = pd.concat([title_overall_results, pd.DataFrame(columns=[
            'expenditures_fuel_annual',
            'expenditures_main_grid_consumption_annual',
            'revenue_main_grid_feedin_annual'])], axis=1, sort=False)

        # Called costs because they include the operation, while they are also not the present value because
        # the variable costs are included in the oem
        if settings['results_costs'] == True:
            title_overall_results = pd.concat([title_overall_results, pd.DataFrame(columns=[
                'costs_pv',
                'costs_storage',
                'costs_genset',
                'costs_pcoupling',
                'costs_distribution_grid',
                'costs_project',
                'costs_grid_extension',
                'expenditures_fuel_total',
                'expenditures_main_grid_consumption_total',
                'revenue_main_grid_feedin_total'])], axis=1, sort=False)

        title_overall_results = pd.concat([title_overall_results, pd.DataFrame(columns=[
            'annuity',
            'npv',
            'lcoe',
            'supply_reliability',
            'objective_value',
            'simulation_time',
            'comments'])], axis=1, sort=False)

        if number_of_project_sites > 1:
            title_overall_results = pd.concat([title_overall_results, pd.DataFrame(columns=['project_site_name'])], axis=1)

        for keys in sensitivity_array_dict:
            title_overall_results = pd.concat([title_overall_results, pd.DataFrame(columns=[keys])], axis=1)

        return title_overall_results

class output:
    def check_output_directory(experiments):
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
            if  experiments[experiment]['restore_oemof_if_existant'] == False:
                for root, dirs, files in os.walk(output_folder):
                    for f in files:
                        os.remove(root + '/' + f)
                logging.info('Deleted all files in folder "simulation_results".')
        return

    def print_oemof_meta_main_invest(experiment, meta, electricity_bus, case_name):
        if experiment['print_simulation_meta'] == True:
            logging.info('********* Meta results *********')
            pp.pprint(meta)

        # print the sums of the flows around the electricity bus
        if experiment['print_simulation_main'] == True:
            logging.info('********* Main results *********')
            pp.pprint(electricity_bus['sequences'].sum(axis=0))

        # print the scalars of investment optimization (not equal to capacities!)
        if case_name == "base_oem" or case_name == "base_oem_with_min_loading":
            if experiment['print_simulation_invest'] == True:
                logging.info('********* Invest results *********')
                pp.pprint(electricity_bus['scalars'])
        return

    def save_mg_flows(experiment, case_dict, e_flows_df, filename):
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

        if experiment['setting_save_flows_storage'] == True:
            mg_flows.to_csv(experiment['output_folder'] + '/electricity_mg/' + case_dict['case_name'] + filename + '_electricity_mg.csv')

        if experiment['display_graphs_flows_electricity_mg'] == True:
            fig = mg_flows.plot(title = 'MG Operation of case ' + case_dict['case_name'])
            fig.set(xlabel='Time', ylabel='Electricity flow in kWh')
            fig.legend(loc='upper right')
            plt.savefig(experiment['output_folder'] + '/electricity_mg/' + case_dict['case_name'] + filename + '_electricity_mg.png')
            plt.clf()
            # todo change if 15-min intervals
            if (len(mg_flows['Demand']) >= 7 * 24):
                fig = mg_flows[0:7 * 24].plot(title = 'MG Operation of case ' + case_dict['case_name'])
                fig.set(xlabel='Time', ylabel='Electricity flow in kWh')
                fig.legend(loc='upper right')
                plt.savefig(experiment['output_folder'] + '/electricity_mg/' + case_dict['case_name'] + filename + '_electricity_mg_7days.png')
                plt.close()
        return

    def save_storage(experiment, case_dict, e_flows_df, filename):
        if case_dict['storage_fixed_capacity'] != None:

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

            if experiment['setting_save_flows_storage'] == True:
                storage_flows.to_csv(experiment['output_folder'] + '/storage/' + case_dict['case_name'] + filename + '_storage.csv')

            if experiment['display_graphs_flows_storage'] == True:
                fig = storage_flows.plot(title = 'Storage flows of case ' + case_dict['case_name'])
                fig.set(xlabel='Time', ylabel='Electricity flow/stored in kWh')
                fig.legend(loc='upper right')
                plt.savefig(experiment['output_folder'] + '/storage/' + case_dict['case_name'] + filename + '_storage.png')
                plt.clf()
                #todo change if 15-min intervals
                if (len(storage_flows['Stored capacity']) >= 7*24):
                    fig = storage_flows[0:7*24].plot(title='Storage flows of case ' + case_dict['case_name'])
                    fig.set(xlabel='Time', ylabel='Electricity flow/stored in kWh')
                    fig.legend(loc='upper right')
                    plt.savefig(experiment['output_folder'] + '/storage/' + case_dict['case_name'] + filename + '_storage_7days.png')
                    plt.close()
        return
