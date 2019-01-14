'''
Overlying script for tool for the analysis of possible
operational modes of micro grids interconnecting with an unreliable national grid

General settings from config.py, simulation-specific input data taken from dictionary experiment

Utilizing the bus/component library oemof_generatemodel and the process oemof library oemof_general
new cases can easily be added.
'''

# to check for files and paths
import os.path

# Logging of info
import logging
import oemof.outputlib as outputlib

# For speeding up lp_files and bus/component definition in oemof as well as processing
from oemof_create_model import oemof_model
from case_definitions import utilities
from timeseries import timeseries
from plausability_tests import plausability_tests
from output_functions import output
from economic_evaluation import economic_evaluation
import constraints_custom as constraints

# This is not really a necessary class, as the whole experiement could be given to the function, but it ensures, that
# only correct input data is included

class oemof_simulate:

    def run(experiment, case_dict, demand_profile, pv_generation_per_kWp, grid_availability):
        from config import output_folder, restore_oemof_if_existant
        '''
        Funktion to generate oemof-lp file, simulate and extract simulation results from oemof-results,
        including extraction of time series, accumulated values, optimized capacities.
        Simulation results are extracted based on their case definitions in case_dict,
        thus the only part where changes are neccesary to modify cases is not here but
        in the case definitions directly (oemof_cases). If the computation of the extracted
        results itself should change (eg. in the future allowing a finer timestep resulution),
        this is the right place.
        '''

        file_name = utilities.filename(case_dict['case_name'], experiment['filename'])
        utilities.extend_dictionary(case_dict, experiment, demand_profile)

        # For restoring .oemof results if that is possible (speeding up computation time)
        if os.path.isfile(output_folder + "/oemof/" + file_name + ".oemof") and restore_oemof_if_existant == True:
            logging.info("Previous results of " + case_dict['case_name'] + " restored.")

        # If .oemof results do not already exist, start oemof-process
        else:
            # generate model
            micro_grid_system, model = oemof_model.build(experiment, case_dict, demand_profile, pv_generation_per_kWp, grid_availability)
            # perform simulation
            micro_grid_system        = oemof_model.simulate(micro_grid_system, model, file_name)
            # store simulation results to .oemof
            oemof_model.store_results(micro_grid_system, file_name)

        # it actually is not really necessary to restore just simulated results... but for consistency and to make sure that calling results is easy, this is used nevertheless
        # load oemof results from previous or just finished simulation
        micro_grid_system = oemof_model.load_oemof_results(file_name)
        # process results
        pv_generation_max = max(pv_generation_per_kWp)

        ######################
        # Processing
        ######################
        results = micro_grid_system.results['main']
        meta = micro_grid_system.results['meta']

        oemof_results = {
            'case': case_dict['case_name'],
            'filename': 'results_' + case_dict['case_name'] + experiment['filename'],
            'objective_value': meta['objective'],
            'comments': ''
        }

        # get all from node electricity bus
        electricity_bus = outputlib.views.node(results, 'bus_electricity_mg')
        e_flows_df = timeseries.get_demand(case_dict, oemof_results, electricity_bus)
        e_flows_df = timeseries.get_shortage(case_dict, oemof_results, electricity_bus, e_flows_df)
        # todo specify reliability into supply_reliability_kWh, national_grid_reliability_h
        oemof_results.update({'supply_reliability':
                                  oemof_results['total_demand_supplied_annual_kWh'] / oemof_results[
                                      'total_demand_annual_kWh']})

        e_flows_df = timeseries.get_excess(case_dict, oemof_results, electricity_bus, e_flows_df)
        e_flows_df = timeseries.get_pv(case_dict, oemof_results, electricity_bus, e_flows_df, pv_generation_max)
        e_flows_df = timeseries.get_genset(case_dict, oemof_results, electricity_bus, e_flows_df)
        e_flows_df = timeseries.get_storage(case_dict, oemof_results, experiment, results, e_flows_df)
        timeseries.get_fuel(case_dict, oemof_results, results)

        # todo still decide with of the flows to include in e_flow_df, and which ones to put into oemof results for cost calculation (expenditures, revenues)
        e_flows_df = timeseries.get_national_grid(case_dict, oemof_results, results, e_flows_df, grid_availability)
        timeseries.get_res_share(case_dict, oemof_results, experiment)

        plausability_tests.run(oemof_results, e_flows_df)

        # todo this is not jet implemented!
        constraints.stability_test(case_dict, oemof_results, experiment, e_flows_df)

        # todo this has to be at end using e_flows_df, has to be edited
        output.outputs_mg_flows(case_dict, e_flows_df, experiment['filename'])
        output.outputs_storage(case_dict, e_flows_df, experiment['filename'])

        output.print_oemof_meta_main_invest(meta, electricity_bus, case_dict['case_name'])

        oemof_results = economic_evaluation.project_annuities(case_dict, oemof_results, experiment)

        logging.info('Simulation of case "' + case_dict['case_name'] + '" resulted in : \n'
                     + '    ' + '  ' + '    ' + '    ' + '    '
                     + str(round(oemof_results['lcoe']*100, 1)) + ' EuroCt/kWh, '
                     + 'at a renewable share of '
                     + str(round(oemof_results['res_share'] * 100, 2)) + ' percent'
                     + ' with a reliability of '
                     + str(round(oemof_results['supply_reliability'] * 100, 2)) + ' percent')

        logging.debug('    Exact OEM results of case "' + case_dict['case_name'] + '" : \n'
                     + '    ' + '  ' + '    ' + '    ' + '    ' + str(
            round(oemof_results['capacity_storage_kWh'], 3)) + ' kWh battery, '
                     + str(round(oemof_results['capacity_pv_kWp'], 3)) + ' kWp PV, '
                     + str(round(oemof_results['capacity_genset_kW'], 3)) + ' kW genset '
                     + 'at a renewable share of ' + str(round(oemof_results['res_share'] * 100, 2)) + ' percent'
                     + ' with a reliability of ' + str(
            round(oemof_results['supply_reliability'] * 100, 2)) + ' percent')

        return oemof_results