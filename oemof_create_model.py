import logging
from oemof_busses_and_componets import generatemodel

class oemof_model():


    def load_energysystem_lp():
        # based on lp file
        return

    def filename(case_name, experiment_name):
        from config import output_file
        file_name = output_file + "_" + case_name + experiment_name
        return file_name

    def case_dictionary(case_name, experiment, total_demand, peak_demand):
        from config import allow_shortage

        case_dict={
            'total_demand': total_demand,
            'peak_demand': peak_demand,
            'pv_fixed_capacity': False, # False, float oder none (non existant component)
            'storage_fixed_capacity': False,
            'genset_fixed_capacity': False,
            'pcc_consumption_fixed_capacity': peak_demand,
            'pcc_feedin_fixed_capacity': peak_demand,
            'allow_shortage': allow_shortage,
            'max_shortage': experiment['max_share_unsupplied_load'],
            'stability_constraint': experiment['stability_limit'], # False or float
            'renewable_share_constraint': experiment['min_renewable_share'] # false or float
        }

        return case_dict

def oemof_model:

    def build(case_name, case_dict):
        from config import date_time_index
        logging.debug('Initialize energy system dataframe')
        # create energy system

        micro_grid_system = solph.EnergySystem(timeindex=date_time_index)

        if case_name in []:
            logging.debug('FIXED CAPACITIES (Dispatch optimization)')
            logging.debug('Create oemof objects for Micro Grid System (off-grid)')

        else:
            logging.debug('VARIABLE CAPACITIES (OEM)')
            logging.debug('Create oemof objects for Micro Grid System (off-grid)')

        bus_fuel = solph.Bus(label="bus_fuel")
        bus_electricity_mg = solph.Bus(label="bus_electricity_mg")
        micro_grid_system.add(bus_electricity_mg, bus_fuel)

        # todo can be without limit if constraint is inluded
        # todo define total_demand as entry of experiment eraly on! needed for generatemodel.fuel_oem
        # add fuel source
        if case_name in []:
            generatemodel.fuel_oem(micro_grid_system, bus_fuel, experiment, total_demand)
        else:
            fuel_fix(micro_grid_system, bus_fuel, experiment)
        # add demand sink
        sink_demand = generatemodel.demand(micro_grid_system, bus_electricity_mg, demand_profile)
        # add excess sink
        generatemodel.excess(micro_grid_system, bus_electricity_mg)

        if case_dict['pcc_consumption_fixed_capacity'] != None or case_dict['pcc_feedin_fixed_capacity'] != None:
            bus_electricity_ng = solph.Bus(label="bus_electricity_ng")
            micro_grid_system.add(bus_electricity_ng)

        if case_dict['pcc_consumption_fixed_capacity']:
            maingrid_consumption(micro_grid_system, bus_electricity_ng, experiment, grid_availability):

        if case_dict['pcc_feedin_fixed_capacity']:
            maingrid_feedin(micro_grid_system, bus_electricity_ng, experiment, grid_availability):

        '''
        Adding pv to the system 
        '''
        case_dict=[]
        if case_dict['pv_fixed_capacity']==None:
            pass # no pv created

        elif case_dict['pv_fixed_capacity']==False:
            generatemodel.pv_oem(micro_grid_system, bus_electricity_mg, pv_generation, experiment)

        elif isinstance(case_dict[''], float):
            micro_grid_system, bus_electricity_mg = pv_fix(micro_grid_system, bus_electricity_mg, pv_generation_per_kWp,
                                                           capacity_pv, experiment):

        else:
            logging.warning('Case definition of ' + case_name
                            + ' faulty at pv_fixed_capacity. Value can only be False, float or None')

        '''
        Adding genset to the system 
        '''

        if case_dict[''] == None:
            pass
        elif case_dict[''] = False:
            transformer_fuel_generator = generatemodel.genset_oem(micro_grid_system, bus_fuel, bus_electricity_mg, experiment)

        elif isinstance(case_dict[''], float):
            micro_grid_system, bus_fuel, bus_electricity_mg, transformer_fuel_generator = genset_fix(micro_grid_system,
                                                                                                     bus_fuel,
                                                                                                     bus_electricity_mg,
                                                                                                     capacity_fuel_gen,
                                                                                                     experiment)
        else:
            logging.warning('Case definition of ' + case_name
                            + ' faulty at genset_fixed_capacity. Value can only be False, float or None')

        '''
        Adding storage to the system 
        '''
        if case_dict[''] == None:
            pass
        elif case_dict[''] = False:
            storage = generatemodel.storage_oem(micro_grid_system, bus_electricity_mg, experiment)

        elif isinstance(case_dict[''], float):
            micro_grid_system, bus_electricity_mg, generic_storage = storage_fix(micro_grid_system, bus_electricity_mg,
                                                                                 capacity_storage, experiment):

            else:
            logging.warning('Case definition of ' + case_name
                            + ' faulty at genset_fixed_capacity. Value can only be False, float or None')

        '''
        Adding point of coupling (consumption) to the system 
        '''
        if case_dict[''] == None:
            pass
        elif case_dict[''] = False:
            micro_grid_system, bus_electricity_mg, bus_electricity_ng, pointofcoupling_consumption = pointofcoupling_consumption_oem(
                micro_grid_system, bus_electricity_mg, bus_electricity_ng, experiment)

        elif isinstance(case_dict[''], float):
            micro_grid_system, bus_electricity_mg, bus_electricity_ng, pointofcoupling_consumption = pointofcoupling_consumption_fix(
                micro_grid_system, bus_electricity_mg, bus_electricity_ng, cap_pointofcoupling, experiment)

        else:
            logging.warning('Case definition of ' + case_name
                            + ' faulty at genset_fixed_capacity. Value can only be False, float or None')

        '''
        Adding point of coupling (feedin) to the system 
        '''
        if case_dict[''] == None:
            pass
        elif case_dict[''] = False:
            # todo point of coupling = max(demand) limits PV feed-in, therefore there should be a minimal pcc capacity defined with
            # optimal larger size though OEM. existing = min_cap_pointofcoupling. but are all costs included?
            # ERROR-Optimization failed with status ok and terminal condition unbounded when using existing = min_cap_pointofcoupling
            micro_grid_system, bus_electricity_mg, bus_electricity_ng, pointofcoupling_feedin = pointofcoupling_feedin_oem(
                micro_grid_system, bus_electricity_mg, bus_electricity_ng, min_cap_pointofcoupling, experiment)

        elif isinstance(case_dict[''], float):
            micro_grid_system, bus_electricity_mg, bus_electricity_ng, pointofcoupling_feedin = pointofcoupling_feedin_fix(
                micro_grid_system, bus_electricity_mg, bus_electricity_ng, capacity_pointofcoupling, experiment)

            else:
            logging.warning('Case definition of ' + case_name
                            + ' faulty at genset_fixed_capacity. Value can only be False, float or None')


        if case_dict['allow_shortage'] == True:
            # add source shortage, if allowed
            generatemodel.shortage(micro_grid_system,
                                   bus_electricity_mg,
                                   total_demand=case_dict['total_demand'],
                                   experiment)

        logging.debug('Initialize the energy system to be optimized')
        model = solph.Model(micro_grid_system)

        # add stability constraint
        if isinstance(case_dict['stability_constraint'], float):
            logging.debug('Adding stability constraint.')
            constraints.stability_criterion(model,
                                        stability_limit=case_dict['stability_constraint'],
                                        storage=storage,
                                        sink_demand=sink_demand,
                                        genset=transformer_fuel_generator,
                                        el_bus=bus_electricity_mg)


        renewable_share_criterion(model, 
                                  experiment = experiment, 
                                  total_demand = case_dict['total_demand'],
                                  genset = transformer_fuel_generator, 
                                  pcc_consumption = ,
                                  el_bus=bus_electricity_mg)



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

