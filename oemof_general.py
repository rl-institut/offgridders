"""
Requires:
oemof, matplotlib, demandlib, pvlib
tables, tkinter
"""

###############################################################################
# Imports and initialize
###############################################################################

# from oemof.tools import helpers
import pprint as pp
import pandas as pd
import oemof.solph as solph
import oemof.outputlib as outputlib
import logging

# Try to import matplotlib librar
try:
    import matplotlib.pyplot as plt
except ImportError:
    logging.warning('Attention! matplotlib could not be imported.')
    plt = None

###############################################################################
# Define all oemof_functioncalls (including generate graph etc)
###############################################################################

class oemofmodel():
    ######## Textblocks ########
    def textblock_fix():
        logging.debug('    FIXED CAPACITIES (Dispatch optimization)')
        logging.debug('Create oemof objects for Micro Grid System (off-grid)')

    def textblock_oem():
        logging.debug('    VARIABLE CAPACITIES (OEM)')
        logging.debug('Create oemof objects for Micro Grid System (off-grid)')
    ######## Textblocks ########

    ######## Simulation control ########
    def initialize_model():
        from config import date_time_index
        logging.debug('Initialize energy system dataframe')
        # create energy system
        micro_grid_system = solph.EnergySystem(timeindex=date_time_index)
        return micro_grid_system

    def simulate(micro_grid_system):
        from config import solver, solver_verbose, output_folder, output_file, setting_lp_file
        logging.debug('Initialize the energy system to be optimized')
        model = solph.Model(micro_grid_system)
        logging.debug('Solve the optimization problem')
        model.solve(solver=solver,
                    solve_kwargs={'tee': solver_verbose})  # if tee_switch is true solver messages will be displayed
        if setting_lp_file == True: model.write('./my_model.lp', io_options={'symbolic_solver_labels': True})

        # add results to the energy system to make it possible to store them.
        micro_grid_system.results['main'] = outputlib.processing.results(model)
        micro_grid_system.results['meta'] = outputlib.processing.meta_results(model)
        return micro_grid_system
    ######## Simulation control ########

    ######## Processing ########
    def load_energysystem():
        return

    def store_results(micro_grid_system, case_name):
        # todo Enter check for directory and create directory here!
        # store energy system with results
        from config import output_folder, output_file
        micro_grid_system.dump(dpath=output_folder, filename=output_file+ '_' + case_name + ".oemof")
        logging.debug('Stored results in ' + output_folder + '/' + output_file + '_' + case_name + '.oemof')
        return micro_grid_system

    def load_results():
        from config import output_folder, output_file
        logging.debug('Restore the energy system and the results.')
        micro_grid_system = solph.EnergySystem()
        micro_grid_system.restore(dpath=output_folder, filename=output_file+".oemof")
        return micro_grid_system

    def process(micro_grid_system, case_name, get_el_bus):
        from config import print_simulation_meta, print_simulation_main
        # define an alias for shorter calls below (optional)
        results = micro_grid_system.results['main']
        meta = micro_grid_system.results['meta']
        storage = micro_grid_system.groups['generic_storage']

        # get all variables of a specific component/bus
        generic_storage = outputlib.views.node(results, 'generic_storage')
        electricity_bus = outputlib.views.node(results, 'bus_electricity_mg')
        oemofmodel.plot_el_mg(electricity_bus)
        oemofmodel.plot_storage(generic_storage)

        # print the solver results
        if print_simulation_meta == True:
            logging.info('********* Meta results *********')
            pp.pprint(meta)
        # print the sums of the flows around the electricity bus
        if print_simulation_main == True:
            logging.info('********* Main results *********')
            pp.pprint(electricity_bus['sequences'].sum(axis=0))

        if get_el_bus == True:
            return electricity_bus
        else:
            return logging.info('    Dispatch optimization for case "' + case_name + '" finished, with renewable share of ' +
            str(round(abs(1 - electricity_bus['sequences'][(('transformer_fuel_generator', 'bus_electricity_mg'), 'flow')].sum()
             / electricity_bus['sequences'][(('bus_electricity_mg', 'sink_demand'), 'flow')].sum()) * 100)) +
                                ' percent.')

    def process_oem(electricity_bus, case_name, pv_generation_max):
        oem_results = {'storage_invest_kWh': electricity_bus['scalars'][(('generic_storage', 'bus_electricity_mg'), 'invest')],
                                           'pv_invest_kW': electricity_bus['scalars'][(('source_pv', 'bus_electricity_mg'), 'invest')]*pv_generation_max,
                                           'genset_invest_kW': electricity_bus['scalars'][(('transformer_fuel_generator', 'bus_electricity_mg'), 'invest')],
                                           'res_share_perc': abs(1 - electricity_bus['sequences'][(('transformer_fuel_generator', 'bus_electricity_mg'), 'flow')].sum()
                                                          / electricity_bus['sequences'][(('bus_electricity_mg', 'sink_demand'), 'flow')].sum())*100}

        logging.info ('    The exact OEM results of case "' + case_name + '" : \n'
                      + '    ' + '    ' + '    ' + str(round(oem_results['storage_invest_kWh'],3)) + ' kWh battery, '
                      + str(round(oem_results['pv_invest_kW'],3)) + ' kWp PV, '
                      + str(round(oem_results['genset_invest_kW'],3)) + ' kW genset '
                      + 'at a renewable share of ' + str(round(oem_results['res_share_perc'],3)) + ' percent.')

        return oem_results

    def process_oem_batch(capacities_base, case_name):
        from config import round_to_batch
        capacities_base.update({'pv_invest_kW': round (0.5+capacities_base['pv_invest_kW']/round_to_batch['PV'])
                                                  *round_to_batch['PV']}) # immer eher 0.25 capacity mehr als eigentlich nötig
        capacities_base.update({'genset_invest_kW': round(0.5+capacities_base['genset_invest_kW'] / round_to_batch['GenSet']) *
                                                  round_to_batch['GenSet']})
        capacities_base.update({'storage_invest_kWh': round(0.5+capacities_base['storage_invest_kWh'] / round_to_batch['Storage']) *
                                                  round_to_batch['Storage']})
        logging.info ('    The equivalent batch capacities of the base case OEM for case "' + case_name + '" are: \n'
                      + '    ' + '    ' + '    ' + str(capacities_base['storage_invest_kWh']) + ' kWh battery, '
                      + str(capacities_base['pv_invest_kW']) + ' kWp PV, '
                      + str(capacities_base['genset_invest_kW']) + ' kW genset '
                      + 'at a renewable share of ' + str(round(capacities_base['res_share_perc'],2)) + ' percent.')
        return capacities_base
    ######## Processing ########

    ####### Show #######
    def plot_storage(custom_storage):
        from config import display_graphs_simulation
        if plt is not None and display_graphs_simulation == True:
            logging.debug('Plotting: Generic storage')
            custom_storage['sequences'][(('generic_storage', 'None'), 'capacity')].plot(kind='line',
                                                                                        drawstyle='steps-post',
                                                                                        label='??((generic_storage, None), capacity)??')
            custom_storage['sequences'][(('generic_storage', 'bus_electricity_mg'), 'flow')].plot(kind='line',
                                                                                                  drawstyle='steps-post',
                                                                                                  label='Discharge storage')
            custom_storage['sequences'][(('bus_electricity_mg', 'generic_storage'), 'flow')].plot(kind='line',
                                                                                                  drawstyle='steps-post',
                                                                                                  label='Charge storage')
            plt.legend(loc='upper right')
            plt.show()
        return

    def plot_el_mg(electricity_bus):
        from config import allow_shortage, display_graphs_simulation
        if plt is not None and display_graphs_simulation == True:
            logging.debug('Plotting: Electricity bus')
            # plot each flow to/from electricity bus with appropriate name
            electricity_bus['sequences'][(('source_pv', 'bus_electricity_mg'), 'flow')].plot(kind='line',
                                                                                             drawstyle='steps-post',
                                                                                             label='PV generation')
            electricity_bus['sequences'][(('bus_electricity_mg', 'sink_demand'), 'flow')].plot(kind='line',
                                                                                               drawstyle='steps-post',
                                                                                               label='Demand supply')
            electricity_bus['sequences'][(('transformer_fuel_generator', 'bus_electricity_mg'), 'flow')].plot(
                kind='line', drawstyle='steps-post', label='GenSet')
            electricity_bus['sequences'][(('generic_storage', 'bus_electricity_mg'), 'flow')].plot(kind='line',
                                                                                                   drawstyle='steps-post',
                                                                                                   label='Discharge storage')
            electricity_bus['sequences'][(('bus_electricity_mg', 'generic_storage'), 'flow')].plot(kind='line',
                                                                                                   drawstyle='steps-post',
                                                                                                   label='Charge storage')
            electricity_bus['sequences'][(('bus_electricity_mg', 'sink_excess'), 'flow')].plot(kind='line',
                                                                                               drawstyle='steps-post',
                                                                                               label='Excess electricity')
            if allow_shortage == True: electricity_bus['sequences'][
                (('source_shortage', 'bus_electricity_mg'), 'flow')].plot(kind='line', drawstyle='steps-post',
                                                                          label='Supply shortage')
            plt.legend(loc='upper right')
            plt.show()
        return
    ###### Show ######