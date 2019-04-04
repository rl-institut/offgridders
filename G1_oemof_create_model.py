import logging
import oemof.solph as solph
import oemof.outputlib as outputlib
from G2a_oemof_busses_and_componets import generate
from G2b_constraints_custom import stability_criterion, renewable_criterion, battery_management, ac_dc_bus, shortage_constraints

class oemof_model:

    def load_energysystem_lp():
        # based on lp file
        return

    def build(experiment, case_dict):
        logging.debug('Create oemof model by adding case-specific busses and components.')

        # create energy system
        micro_grid_system = solph.EnergySystem(timeindex=experiment['date_time_index'])

        ###################################
        ## AC side of the energy system   #
        ###################################

        #------------AC electricity bus------------#
        if case_dict['genset_fixed_capacity'] != None \
                or case_dict['wind_fixed_capacity'] != None \
                or case_dict['pcc_consumption_fixed_capacity'] != None \
                or case_dict['pcc_feedin_fixed_capacity'] != None:

            logging.debug('Added to oemof model: Electricity bus of energy system, AC')
            bus_electricity_ac = solph.Bus(label="bus_electricity_ac")
            micro_grid_system.add(bus_electricity_ac)
        else:
            bus_electricity_ac = None

        # ------------demand sink ac------------#
        sink_demand_ac = generate.demand_ac(micro_grid_system, bus_electricity_ac, experiment['demand_profile_ac'])

        #------------fuel source------------#
        if case_dict['genset_fixed_capacity']!=None:
            logging.debug('Added to oemof model: Fuel bus')
            bus_fuel = solph.Bus(label="bus_fuel")
            micro_grid_system.add(bus_fuel)
            generate.fuel(micro_grid_system, bus_fuel, experiment)

        #------------genset------------#
        if case_dict['genset_fixed_capacity'] == None:
            genset = None
        elif case_dict['genset_fixed_capacity'] == False:
            if case_dict['genset_with_minimal_loading']==True:
                # not possible with oemof
                genset = generate.genset_oem_minload(micro_grid_system, bus_fuel, bus_electricity_ac, experiment, case_dict['number_of_equal_generators'])
            else:
                genset = generate.genset_oem(micro_grid_system, bus_fuel, bus_electricity_ac, experiment,
                                                             case_dict['number_of_equal_generators'])

        elif isinstance(case_dict['genset_fixed_capacity'], float):
            if case_dict['genset_with_minimal_loading'] == True:
                genset = generate.genset_fix_minload(micro_grid_system, bus_fuel,
                                                             bus_electricity_ac, experiment,
                                                             capacity_fuel_gen=case_dict['genset_fixed_capacity'],
                                                     number_of_equal_generators=case_dict['number_of_equal_generators'])
            else:
                genset = generate.genset_fix(micro_grid_system, bus_fuel,
                                                             bus_electricity_ac, experiment,
                                                             capacity_fuel_gen=case_dict['genset_fixed_capacity'],
                                             number_of_equal_generators=case_dict['number_of_equal_generators'])
        else:
            logging.warning('Case definition of ' + case_dict['case_name']
                            + ' faulty at genset_fixed_capacity. Value can only be False, float or None')

        #------------wind------------#
        if case_dict['wind_fixed_capacity']==None:
            wind_plant = None
        elif case_dict['wind_fixed_capacity']==False:
            wind_plant = generate.wind_oem(micro_grid_system, bus_electricity_ac, experiment)

        elif isinstance(case_dict['wind_fixed_capacity'], float):
            wind_plant = generate.wind_fix(micro_grid_system, bus_electricity_ac, experiment,
                            capacity_wind=case_dict['wind_fixed_capacity'])

        else:
            logging.warning('Case definition of ' + case_dict['case_name']
                            + ' faulty at wind_fixed_capacity. Value can only be False, float or None')

        #------------ main grid bus and subsequent sources if necessary------------#
        if case_dict['pcc_consumption_fixed_capacity'] != None:
            # source + sink for electricity from grid
            bus_electricity_ng_consumption = generate.maingrid_consumption(micro_grid_system, experiment)

        if case_dict['pcc_feedin_fixed_capacity'] != None:
            # sink + source for feed-in
            bus_electricity_ng_feedin = generate.maingrid_feedin(micro_grid_system, experiment)

        #------------point of coupling (consumption)------------#
        if case_dict['pcc_consumption_fixed_capacity'] == None:
            pointofcoupling_consumption = None
        elif case_dict['pcc_consumption_fixed_capacity'] == False:
            pointofcoupling_consumption = generate.pointofcoupling_consumption_oem(micro_grid_system, bus_electricity_ac,
                                                                                   bus_electricity_ng_consumption, experiment,
                                                                                   min_cap_pointofcoupling=case_dict['peak_demand'])
        elif isinstance(case_dict['pcc_consumption_fixed_capacity'], float):
            pointofcoupling_consumption = generate.pointofcoupling_consumption_fix(micro_grid_system, bus_electricity_ac,
                                                                                   bus_electricity_ng_consumption, experiment,
                                                                                   cap_pointofcoupling=case_dict['pcc_consumption_fixed_capacity'])
        else:
            logging.warning('Case definition of ' + case_dict['case_name']
                            + ' faulty at pcc_consumption_fixed_capacity. Value can only be False, float or None')


        #------------point of coupling (feedin)------------#
        if case_dict['pcc_feedin_fixed_capacity'] == None:
            pass
            #pointofcoupling_feedin = None
        elif case_dict['pcc_feedin_fixed_capacity'] == False:
            generate.pointofcoupling_feedin_oem(micro_grid_system, bus_electricity_ac,
                                                bus_electricity_ng_feedin, experiment,
                                                                         min_cap_pointofcoupling=case_dict['peak_demand'])

        elif isinstance(case_dict['pcc_feedin_fixed_capacity'], float):
            generate.pointofcoupling_feedin_fix(micro_grid_system, bus_electricity_ac,
                                                bus_electricity_ng_feedin, experiment,
                                                                         capacity_pointofcoupling=case_dict['pcc_feedin_fixed_capacity'])
        else:
            logging.warning('Case definition of ' + case_dict['case_name']
                            + ' faulty at pcc_feedin_fixed_capacity. Value can only be False, float or None')

        ###################################
        ## DC side of the energy system   #
        ###################################

        #------------DC electricity bus------------#
        if case_dict['pv_fixed_capacity']!=None \
                or case_dict['storage_fixed_capacity'] != None:

            logging.debug('Added to oemof model: Electricity bus of energy system, DC')
            bus_electricity_dc = solph.Bus(label="bus_electricity_dc")
            micro_grid_system.add(bus_electricity_dc)
        else:
            bus_electricity_dc = None

        #------------demand sink dc------------#
        sink_demand_dc = generate.demand_dc(micro_grid_system, bus_electricity_dc, experiment['demand_profile_dc'])

        #------------PV------------#
        if case_dict['pv_fixed_capacity']==None:
            solar_plant = None
        elif case_dict['pv_fixed_capacity']==False:
            solar_plant = generate.pv_oem(micro_grid_system, bus_electricity_dc, experiment)

        elif isinstance(case_dict['pv_fixed_capacity'], float):
            solar_plant = generate.pv_fix(micro_grid_system, bus_electricity_dc, experiment,
                            capacity_pv=case_dict['pv_fixed_capacity'])

        else:
            logging.warning('Case definition of ' + case_dict['case_name']
                            + ' faulty at pv_fixed_capacity. Value can only be False, float or None')

        #------------storage------------#
        if case_dict['storage_fixed_capacity'] == None:
            storage = None
        elif case_dict['storage_fixed_capacity'] == False:
            storage = generate.storage_oem(micro_grid_system, bus_electricity_dc, experiment)

        elif isinstance(case_dict['storage_fixed_capacity'], float):
            storage = generate.storage_fix(micro_grid_system, bus_electricity_dc, experiment,
                                           capacity_storage=case_dict['storage_fixed_capacity']) # changed order

        else:
            logging.warning('Case definition of ' + case_dict['case_name']
                            + ' faulty at genset_fixed_capacity. Value can only be False, float or None')


        #------------Rectifier AC DC------------#
        if case_dict['rectifier_ac_dc_fixed_capacity'] == None:
            rectifier = None

        elif case_dict['rectifier_ac_dc_fixed_capacity'] == False:
            rectifier = generate.rectifier_oem(micro_grid_system, bus_electricity_ac, bus_electricity_dc, experiment)

        elif isinstance(case_dict['rectifier_ac_dc_fixed_capacity'], float):
            rectifier = generate.rectifier_fix(micro_grid_system, bus_electricity_ac, bus_electricity_dc, experiment, case_dict['rectifier_ac_dc_fixed_capacity'])

        else:
            logging.warning('Case definition of ' + case_dict['case_name']
                            + ' faulty at rectifier_ac_dc_capacity_. Value can only be False, float or None')

        #------------Inverter DC AC------------#
        if case_dict['inverter_dc_ac_fixed_capacity'] == None:
            inverter = None

        elif case_dict['inverter_dc_ac_fixed_capacity'] == False:
            inverter = generate.inverter_dc_ac_oem(micro_grid_system, bus_electricity_ac, bus_electricity_dc, experiment)

        elif isinstance(case_dict['inverter_dc_ac_fixed_capacity'], float):
            inverter = generate.inverter_dc_ac_fix(micro_grid_system, bus_electricity_ac, bus_electricity_dc, experiment, case_dict['inverter_dc_ac_fixed_capacity'])

        else:
            logging.warning('Case definition of ' + case_dict['case_name']
                            + ' faulty at inverter_dc_ac_capacity. Value can only be False, float or None')

        ###################################
        ## Global sinks / sources         #
        ###################################

        # ------------Excess sink------------#
        generate.excess(micro_grid_system, bus_electricity_ac, bus_electricity_dc)

        #------------Optional: Shortage source------------#
        if case_dict['allow_shortage'] == True:
            source_shortage = generate.shortage(micro_grid_system, bus_electricity_ac, bus_electricity_dc, experiment, case_dict) # changed order
        else:
            source_shortage = None

        logging.debug('Create oemof model based on created components and busses.')
        model = solph.Model(micro_grid_system)


        #------------Stability constraint------------#
        if case_dict['stability_constraint'] == False:
            pass
        elif case_dict['stability_constraint']=='share_backup':
            logging.debug('Adding stability constraint (stability through backup).')
            stability_criterion.backup(model, case_dict,
                                            experiment = experiment,
                                            storage = storage,
                                            sink_demand = sink_demand_ac,
                                            genset = genset,
                                            pcc_consumption = pointofcoupling_consumption,
                                            source_shortage=source_shortage,
                                            el_bus = bus_electricity_ac)
        elif case_dict['stability_constraint']=='share_usage':
            logging.debug('Adding stability constraint (stability though actual generation).')
            stability_criterion.usage(model, case_dict,
                                            experiment = experiment,
                                            storage = storage,
                                            sink_demand = sink_demand_ac,
                                            genset = genset,
                                            pcc_consumption = pointofcoupling_consumption,
                                            source_shortage=source_shortage,
                                            el_bus = bus_electricity_ac)
        elif case_dict['stability_constraint']=='share_hybrid':
            logging.debug('Adding stability constraint (stability though actual generation of diesel generators and backup through batteries).')
            stability_criterion.hybrid(model, case_dict,
                                       experiment = experiment,
                                       storage = storage,
                                       sink_demand = sink_demand_ac,
                                       genset = genset,
                                       pcc_consumption = pointofcoupling_consumption,
                                       source_shortage=source_shortage,
                                       el_bus = bus_electricity_ac)
        else:
            logging.warning('Case definition of ' + case_dict['case_name']
                            + ' faulty at stability_constraint. Value can only be False, float or None')

        # ------------Renewable share constraint------------#
        if case_dict['renewable_share_constraint']==False:
            pass
        elif case_dict['renewable_share_constraint'] == True:
            logging.info('Adding renewable share constraint.')
            renewable_criterion.share(model, case_dict, experiment,
                                      genset = genset,
                                      pcc_consumption = pointofcoupling_consumption,
                                      solar_plant=solar_plant,
                                      wind_plant = wind_plant,
                                      el_bus=bus_electricity_ac)
        else:
            logging.warning('Case definition of ' + case_dict['case_name']
                            + ' faulty at renewable_share_constraint. Value can only be True or False')

        # ------------Force charge from maingrid------------#
        if case_dict['force_charge_from_maingrid']==False:
            pass
        elif case_dict['force_charge_from_maingrid']==True:
            battery_management.forced_charge(model, case_dict, bus_electricity_dc, storage, experiment)
        else:
            logging.warning('Case definition of ' + case_dict['case_name']
                            + ' faulty at force_charge_from_maingrid. Value can only be True or False')


        # ------------Allow discharge only at maingrid blackout------------#
        if case_dict['discharge_only_when_blackout']==False:
            pass
        elif case_dict['discharge_only_when_blackout']==True:
            battery_management.discharge_only_at_blackout(model, case_dict, bus_electricity_dc, storage, experiment)
        else:
            logging.warning('Case definition of ' + case_dict['case_name']
                            + ' faulty at discharge_only_when_blackout. Value can only be True or False')

        # ------------Allow inverter use only at maingrid blackout------------#
        if case_dict['enable_inverter_at_backout']==False:
            pass
        elif case_dict['enable_inverter_at_backout']==True:
            ac_dc_bus.inverter_only_at_blackout(model, case_dict, bus_electricity_dc, inverter, experiment)
        else:
            logging.warning('Case definition of ' + case_dict['case_name']
                            + ' faulty at enable_inverter_at_backout. Value can only be True or False')

        '''
        # ------------Allow inverter use only at maingrid blackout------------#
        if case_dict['allow_shortage'] == True:
            if bus_electricity_ac != None:
                shortage_constraints.timestep(model, case_dict, experiment, sink_demand_ac, 
                                              source_shortage, bus_electricity_ac)
            if bus_electricity_dc != None:
                shortage_constraints.timestep(model, case_dict, experiment, sink_demand_dc, 
                                              source_shortage, bus_electricity_dc)
        '''
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