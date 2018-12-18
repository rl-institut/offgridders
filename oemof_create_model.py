import logging
import oemof.solph as solph
import oemof.outputlib as outputlib
from oemof_busses_and_componets import generate
import constraints_custom as constraints

class oemof_model:

    def load_energysystem_lp():
        # based on lp file
        return

    def filename(case_name, experiment_name):
        from config import output_file
        file_name = output_file + "_" + case_name + experiment_name
        return file_name

    def build(experiment, case_dict, demand_profile, pv_generation_per_kWp, grid_availability):
        from config import date_time_index
        logging.debug('Initialize energy system dataframe')

        # create energy system
        micro_grid_system = solph.EnergySystem(timeindex=date_time_index)

        if case_dict['case_name'] in []:
            logging.debug('FIXED CAPACITIES (Dispatch optimization)')
            logging.debug('Create oemof objects for Micro Grid System (off-grid)')

        else:
            logging.debug('VARIABLE CAPACITIES (OEM)')
            logging.debug('Create oemof objects for Micro Grid System (off-grid)')

        #------        fuel and electricity bus------#
        bus_fuel = solph.Bus(label="bus_fuel")
        bus_electricity_mg = solph.Bus(label="bus_electricity_mg")
        micro_grid_system.add(bus_electricity_mg, bus_fuel)

        # todo can be without limit if constraint is inluded
        # todo define total_demand as entry of experiment eraly on! needed for generatemodel.fuel_oem

        #------        fuel source------#
        if case_dict['case_name'] in []:
            generate.fuel_oem(micro_grid_system, bus_fuel, experiment, case_dict['total_demand'])
        else:
            generate.fuel_fix(micro_grid_system, bus_fuel, experiment)

        #------         main grid bus and subsequent sources if necessary------#
        if case_dict['pcc_consumption_fixed_capacity'] != None or case_dict['pcc_feedin_fixed_capacity'] != None:
            bus_electricity_ng = solph.Bus(label="bus_electricity_ng")
            micro_grid_system.add(bus_electricity_ng)

        if case_dict['pcc_consumption_fixed_capacity']:
            maingrid_consumption(micro_grid_system, bus_electricity_ng, experiment, grid_availability)

        if case_dict['pcc_feedin_fixed_capacity']:
            maingrid_feedin(micro_grid_system, bus_electricity_ng, experiment, grid_availability)

        #------        demand sink ------#
        sink_demand = generate.demand(micro_grid_system, bus_electricity_mg, demand_profile)

        #------        excess sink------#
        generate.excess(micro_grid_system, bus_electricity_mg)

        #------        pv ------#
        if case_dict['pv_fixed_capacity']==None:
            pass # no pv created # todo: or does it make sense to have a pv module with cap 0 for later evaluation?

        elif case_dict['pv_fixed_capacity']==False:
            generate.pv_oem(micro_grid_system, bus_electricity_mg, experiment, pv_generation_per_kWp)

        elif isinstance(case_dict[''], float):
            generate.pv_fix(micro_grid_system, bus_electricity_mg, experiment, pv_generation_per_kWp, capacity_pv=case_dict['pv_fixed_capacity'])

        else:
            logging.warning('Case definition of ' + case_dict['case_name']
                            + ' faulty at pv_fixed_capacity. Value can only be False, float or None')

        #------         genset------#
        if case_dict['genset_fixed_capacity'] == None:
            pass
        elif case_dict['genset_fixed_capacity'] == False:
            transformer_fuel_generator = generate.genset_oem(micro_grid_system, bus_fuel, bus_electricity_mg, experiment)

        elif isinstance(case_dict['genset_fixed_capacity'], float):
            transformer_fuel_generator = generate.genset_fix(micro_grid_system, bus_fuel,
                                                             bus_electricity_mg, experiment,
                                                             capacity_fuel_gen=case_dict['genset_fixed_capacity'])
        else:
            logging.warning('Case definition of ' + case_dict['case_name']
                            + ' faulty at genset_fixed_capacity. Value can only be False, float or None')

        #------         storage------#
        if case_dict['storage_fixed_capacity'] == None:
            pass
        elif case_dict['storage_fixed_capacity'] == False:
            generic_storage = generate.storage_oem(micro_grid_system, bus_electricity_mg, experiment)

        elif isinstance(case_dict['storage_fixed_capacity'], float):
            generic_storage = generate.storage_fix(micro_grid_system, bus_electricity_mg, experiment,
                                           capacity_storage=case_dict['storage_fixed_capacity']) # changed order

        else:
            logging.warning('Case definition of ' + case_dict['case_name']
                            + ' faulty at genset_fixed_capacity. Value can only be False, float or None')

        #------        point of coupling (consumption) ------#
        if case_dict['pcc_consumption_fixed_capacity'] == None:
            pointofcoupling_consumption = None
            pass
        elif case_dict['pcc_consumption_fixed_capacity'] == False:
            # todo min_cap_pointofcoupling should be entry in case_dict
            pointofcoupling_consumption = generate.pointofcoupling_consumption_oem(micro_grid_system, bus_electricity_mg,
                                                                                   bus_electricity_ng, experiment,
                                                                                   min_cap_pointofcoupling=case_dict['peak_demand'])
        elif isinstance(case_dict['pcc_consumption_fixed_capacity'], float):
            pointofcoupling_consumption = generate.pointofcoupling_consumption_fix(micro_grid_system, bus_electricity_mg,
                                                                                   bus_electricity_ng, experiment,
                                                                                   cap_pointofcoupling=case_dict['pcc_consumption_fixed_capacity'])
        else:
            logging.warning('Case definition of ' + case_dict['case_name']
                            + ' faulty at genset_fixed_capacity. Value can only be False, float or None')


        #------point of coupling (feedin)------#
        if case_dict['pcc_feedin_fixed_capacity'] == None:
            pass
        elif case_dict['pcc_feedin_fixed_capacity'] == False:
            pointofcoupling_feedin = generate.pointofcoupling_feedin_oem(micro_grid_system, bus_electricity_mg,
                                                                         bus_electricity_ng, experiment,
                                                                         min_cap_pointofcoupling=case_dict['peak_demand'])

        elif isinstance(case_dict['pcc_feedin_fixed_capacity'], float):
            pointofcoupling_feedin = generate.pointofcoupling_feedin_fix(micro_grid_system, bus_electricity_mg,
                                                                         bus_electricity_ng, experiment,
                                                                         capacity_pointofcoupling=case_dict['pcc_feedin_fixed_capacity'])
        else:
            logging.warning('Case definition of ' + case_dict['case_name']
                            + ' faulty at genset_fixed_capacity. Value can only be False, float or None')

        #------Optional: Shortage source'''
        if case_dict['allow_shortage'] == True:
            generate.shortage(micro_grid_system, bus_electricity_mg, experiment, sum_demand_profile=case_dict['total_demand']) # changed order

        logging.debug('Initialize the energy system to be optimized')
        model = solph.Model(micro_grid_system)

        # add stability constraint
        if case_dict['stability_constraint'] == False:
            pass
        elif isinstance(case_dict['stability_constraint'], float):
            logging.debug('Adding stability constraint.')
            constraints.stability_criterion(model,
                                        stability_limit=case_dict['stability_constraint'],
                                        storage=generic_storage,
                                        sink_demand=sink_demand,
                                        genset=transformer_fuel_generator,
                                        el_bus=bus_electricity_mg)

        else:
            logging.warning('Case definition of ' + case_dict['case_name']
                            + ' faulty at stability_constraint. Value can only be False, float or None')

        if case_dict['renewable_share_constraint']==False:
            pass
        elif isinstance(case_dict['renewable_share_constraint'], float):
            constraints.renewable_share_criterion(model,
                                      experiment = experiment,
                                      total_demand = case_dict['total_demand'],
                                      genset = transformer_fuel_generator,
                                      pcc_consumption = pointofcoupling_consumption,
                                      el_bus=bus_electricity_mg)
        else:
            logging.warning('Case definition of ' + case_dict['case_name']
                            + ' faulty at stability_constraint. Value can only be False, float or None')


        return micro_grid_system, model

    def simulate(micro_grid_system, model, file_name):
        from config import solver, solver_verbose, output_folder, setting_save_lp_file, \
            cmdline_option, cmdline_option_value

        logging.debug('Solve the optimization problem')
        model.solve(solver          =   solver,
                    solve_kwargs    =   {'tee': solver_verbose}, # if tee_switch is true solver messages will be displayed
                    cmdline_options =   {cmdline_option:    str(cmdline_option_value)})   #ratioGap allowedGap mipgap

        if setting_save_lp_file == True:
            model.write(output_folder + '/lp_files/model_' + file_name + '.lp',
                        io_options={'symbolic_solver_labels': True})

        # add results to the energy system to make it possible to store them.
        micro_grid_system.results['main'] = outputlib.processing.results(model)
        micro_grid_system.results['meta'] = outputlib.processing.meta_results(model)
        return micro_grid_system

    def store_results(micro_grid_system, file_name):
        # store energy system with results
        from config import output_folder, setting_save_oemofresults
        if setting_save_oemofresults == True:
            micro_grid_system.dump(dpath=output_folder+'/oemof', filename = file_name + ".oemof" )
            logging.debug('Stored results in ' + output_folder+'/oemof' + '/' + file_name + ".oemof")
        return micro_grid_system

    def load_oemof_results(file_name):
        from config import output_folder
        logging.debug('Restore the energy system and the results.')
        micro_grid_system = solph.EnergySystem()
        micro_grid_system.restore(dpath=output_folder+'/oemof',
                                  filename=file_name + ".oemof")
        return micro_grid_system