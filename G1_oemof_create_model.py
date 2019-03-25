import logging
import oemof.solph as solph
import oemof.outputlib as outputlib
from G2a_oemof_busses_and_componets import generate
from G2b_constraints_custom import stability_criterion, renewable_criterion

class oemof_model:

    def load_energysystem_lp():
        # based on lp file
        return

    def build(experiment, case_dict):
        logging.debug('Create oemof model by adding case-specific busses and components.')

        # create energy system
        micro_grid_system = solph.EnergySystem(timeindex=experiment['date_time_index'])

        #------  micro grid electricity bus------#
        logging.debug('Added to oemof model: Electricity bus')
        bus_electricity_mg = solph.Bus(label="bus_electricity_mg")
        micro_grid_system.add(bus_electricity_mg)
        #------        fuel source------#
        # can be without limit if constraint is inluded
        if case_dict['genset_fixed_capacity']!=None:
            logging.debug('Added to oemof model: Fuel bus')
            bus_fuel = solph.Bus(label="bus_fuel")
            micro_grid_system.add(bus_fuel)
        if case_dict['genset_fixed_capacity'] == False:
            generate.fuel_oem(micro_grid_system, bus_fuel, experiment)
        elif isinstance(case_dict['genset_fixed_capacity'], float):
            generate.fuel_fix(micro_grid_system, bus_fuel, experiment)
        else:
            pass

        #------        demand sink ------#
        sink_demand = generate.demand(micro_grid_system, bus_electricity_mg, experiment['demand_profile'])

        #------        excess sink------#
        generate.excess(micro_grid_system, bus_electricity_mg)

        #------        pv ------#
        if case_dict['pv_fixed_capacity']==None:
            solar_plant = None
        elif case_dict['pv_fixed_capacity']==False:
            solar_plant = generate.pv_oem(micro_grid_system, bus_electricity_mg, experiment)

        elif isinstance(case_dict['pv_fixed_capacity'], float):
            solar_plant = generate.pv_fix(micro_grid_system, bus_electricity_mg, experiment,
                            capacity_pv=case_dict['pv_fixed_capacity'])

        else:
            logging.warning('Case definition of ' + case_dict['case_name']
                            + ' faulty at pv_fixed_capacity. Value can only be False, float or None')

        #------  wind  ------#
        if case_dict['wind_fixed_capacity']==None:
            wind_plant = None
        elif case_dict['wind_fixed_capacity']==False:
            wind_plant = generate.wind_oem(micro_grid_system, bus_electricity_mg, experiment)

        elif isinstance(case_dict['wind_fixed_capacity'], float):
            wind_plant = generate.wind_fix(micro_grid_system, bus_electricity_mg, experiment,
                            capacity_wind=case_dict['wind_fixed_capacity'])

        else:
            logging.warning('Case definition of ' + case_dict['case_name']
                            + ' faulty at wind_fixed_capacity. Value can only be False, float or None')

        #------         genset------#
        if case_dict['genset_fixed_capacity'] == None:
            genset = None
        elif case_dict['genset_fixed_capacity'] == False:
            if case_dict['genset_with_minimal_loading']==True:
                # not possible with oemof
                genset = generate.genset_oem_minload(micro_grid_system, bus_fuel, bus_electricity_mg, experiment, case_dict['number_of_equal_generators'])
            else:
                genset = generate.genset_oem(micro_grid_system, bus_fuel, bus_electricity_mg, experiment,
                                                             case_dict['number_of_equal_generators'])

        elif isinstance(case_dict['genset_fixed_capacity'], float):
            if case_dict['genset_with_minimal_loading'] == True:
                genset = generate.genset_fix_minload(micro_grid_system, bus_fuel,
                                                             bus_electricity_mg, experiment,
                                                             capacity_fuel_gen=case_dict['genset_fixed_capacity'],
                                                     number_of_equal_generators=case_dict['number_of_equal_generators'])
            else:
                genset = generate.genset_fix(micro_grid_system, bus_fuel,
                                                             bus_electricity_mg, experiment,
                                                             capacity_fuel_gen=case_dict['genset_fixed_capacity'],
                                             number_of_equal_generators=case_dict['number_of_equal_generators'])
        else:
            logging.warning('Case definition of ' + case_dict['case_name']
                            + ' faulty at genset_fixed_capacity. Value can only be False, float or None')

        #------storage------#
        if case_dict['storage_fixed_capacity'] == None:
            generic_storage = None
        elif case_dict['storage_fixed_capacity'] == False:
            generic_storage = generate.storage_oem(micro_grid_system, bus_electricity_mg, experiment)

        elif isinstance(case_dict['storage_fixed_capacity'], float):
            generic_storage = generate.storage_fix(micro_grid_system, bus_electricity_mg, experiment,
                                           capacity_storage=case_dict['storage_fixed_capacity']) # changed order

        else:
            logging.warning('Case definition of ' + case_dict['case_name']
                            + ' faulty at genset_fixed_capacity. Value can only be False, float or None')

        #------     main grid bus and subsequent sources if necessary------#
        if case_dict['pcc_consumption_fixed_capacity'] != None:
            # source + sink for electricity from grid
            bus_electricity_ng_consumption = generate.maingrid_consumption(micro_grid_system, experiment)

        if case_dict['pcc_feedin_fixed_capacity'] != None:
            # sink + source for feed-in
            bus_electricity_ng_feedin = generate.maingrid_feedin(micro_grid_system, experiment)

        # ------        point of coupling (consumption) ------#
        if case_dict['pcc_consumption_fixed_capacity'] == None:
            pointofcoupling_consumption = None
        elif case_dict['pcc_consumption_fixed_capacity'] == False:
            pointofcoupling_consumption = generate.pointofcoupling_consumption_oem(micro_grid_system, bus_electricity_mg,
                                                                                   bus_electricity_ng_consumption, experiment,
                                                                                   min_cap_pointofcoupling=case_dict['peak_demand'])
        elif isinstance(case_dict['pcc_consumption_fixed_capacity'], float):
            pointofcoupling_consumption = generate.pointofcoupling_consumption_fix(micro_grid_system, bus_electricity_mg,
                                                                                   bus_electricity_ng_consumption, experiment,
                                                                                   cap_pointofcoupling=case_dict['pcc_consumption_fixed_capacity'])
        else:
            logging.warning('Case definition of ' + case_dict['case_name']
                            + ' faulty at genset_fixed_capacity. Value can only be False, float or None')


        #------point of coupling (feedin)------#
        if case_dict['pcc_feedin_fixed_capacity'] == None:
            pass
            #pointofcoupling_feedin = None
        elif case_dict['pcc_feedin_fixed_capacity'] == False:
            generate.pointofcoupling_feedin_oem(micro_grid_system, bus_electricity_mg,
                                                bus_electricity_ng_feedin, experiment,
                                                                         min_cap_pointofcoupling=case_dict['peak_demand'])

        elif isinstance(case_dict['pcc_feedin_fixed_capacity'], float):
            generate.pointofcoupling_feedin_fix(micro_grid_system, bus_electricity_mg,
                                                bus_electricity_ng_feedin, experiment,
                                                                         capacity_pointofcoupling=case_dict['pcc_feedin_fixed_capacity'])
        else:
            logging.warning('Case definition of ' + case_dict['case_name']
                            + ' faulty at genset_fixed_capacity. Value can only be False, float or None')

        #------Optional: Shortage source'''
        if case_dict['allow_shortage'] == True:
            source_shortage = generate.shortage(micro_grid_system, bus_electricity_mg, experiment, case_dict) # changed order
        else:
            source_shortage = None

        logging.debug('Create oemof model based on created components and busses.')
        model = solph.Model(micro_grid_system)

        if case_dict['stability_constraint'] == False:
            pass
        elif case_dict['stability_constraint']=='share_backup':
            logging.debug('Adding stability constraint (stability through backup).')
            stability_criterion.backup(model, case_dict,
                                            experiment = experiment,
                                            storage = generic_storage,
                                            sink_demand = sink_demand,
                                            genset = genset,
                                            pcc_consumption = pointofcoupling_consumption,
                                            source_shortage=source_shortage,
                                            el_bus = bus_electricity_mg)
        elif case_dict['stability_constraint']=='share_usage':
            logging.debug('Adding stability constraint (stability though actual generation).')
            stability_criterion.usage(model, case_dict,
                                            experiment = experiment,
                                            storage = generic_storage,
                                            sink_demand = sink_demand,
                                            genset = genset,
                                            pcc_consumption = pointofcoupling_consumption,
                                            source_shortage=source_shortage,
                                            el_bus = bus_electricity_mg)
        elif case_dict['stability_constraint']=='share_hybrid':
            logging.debug('Adding stability constraint (stability though actual generation of diesel generators and backup through batteries).')
            stability_criterion.hybrid(model, case_dict,
                                       experiment = experiment,
                                       storage = generic_storage,
                                       sink_demand = sink_demand,
                                       genset = genset,
                                       pcc_consumption = pointofcoupling_consumption,
                                       source_shortage=source_shortage,
                                       el_bus = bus_electricity_mg)
        else:
            logging.warning('Case definition of ' + case_dict['case_name']
                            + ' faulty at stability_constraint. Value can only be False, float or None')

        if case_dict['renewable_share_constraint']==False:
            pass
        elif case_dict['renewable_share_constraint'] == True:
            logging.info('Adding renewable share constraint.')
            renewable_criterion.share(model, case_dict, experiment,
                                      genset = genset,
                                      pcc_consumption = pointofcoupling_consumption,
                                      solar_plant=solar_plant,
                                      wind_plant = wind_plant,
                                      el_bus=bus_electricity_mg)
        else:
            logging.warning('Case definition of ' + case_dict['case_name']
                            + ' faulty at stability_constraint. Value can only be False, float or None')


        return micro_grid_system, model

    def simulate(experiment, micro_grid_system, model, file_name):
        logging.debug('Solve the optimization problem')
        model.solve(solver          =   experiment['solver'],
                    solve_kwargs    =   {'tee': experiment['solver_verbose']}, # if tee_switch is true solver messages will be displayed
                    cmdline_options =   {experiment['cmdline_option']:    str(experiment['cmdline_option_value'])})   #ratioGap allowedGap mipgap
        logging.debug('Problem solved')

        if experiment['save_lp_file'] == True:
            logging.debug('Saving lp-file to folder.')
            model.write(experiment['output_folder'] + '/lp_files/model_' + file_name + '.lp',
                        io_options={'symbolic_solver_labels': True})

        # add results to the energy system to make it possible to store them.
        micro_grid_system.results['main'] = outputlib.processing.results(model)
        micro_grid_system.results['meta'] = outputlib.processing.meta_results(model)
        return micro_grid_system

    def store_results(micro_grid_system, file_name, output_folder):
        # store energy system with results
        micro_grid_system.dump(dpath=output_folder+'/oemof', filename = file_name + ".oemof" )
        logging.debug('Stored results in ' + output_folder+'/oemof' + '/' + file_name + ".oemof")
        return micro_grid_system

    def load_oemof_results(output_folder, file_name):
        logging.debug('Restore the energy system and the results.')
        micro_grid_system = solph.EnergySystem()
        micro_grid_system.restore(dpath=output_folder+'/oemof',
                                  filename=file_name + ".oemof")
        return micro_grid_system