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
#from oemof.tools import logger
import logging

# For speeding up lp_files and bus/component definition in oemof as well as processing
from oemof_create_model import oemof_model
from oemof_process_results import oemof_process
from timeseries import evaluate_timeseries

# This is not really a necessary class, as the whole experiement could be given to the function, but it ensures, that
# only correct input data is included

class cases:

    def extend_dictionary(case_dict, experiment, demand_profile):
        from config import include_stability_constraint, allow_shortage, evaluated_days

        case_dict.update({
            'total_demand': sum(demand_profile),
            'peak_demand': max(demand_profile)
        })

        # shortage if allowed, otherwise zero
        if 'allow_shortage' in case_dict and 'max_shortage' in case_dict:
                pass
        elif 'allow_shortage' in case_dict and case_dict['allow_shortage']==True:
                case_dict.update({'max_shortage': experiment['max_share_unsupplied_load']})
        elif 'allow_shortage' in case_dict and case_dict['allow_shortage'] == False:
                case_dict.update({'max_shortage': 0})
        elif allow_shortage == True:
            case_dict.update({'allow_shortage': True})
            case_dict.update({'max_shortage': experiment['max_share_unsupplied_load']})
        else:
            case_dict.update({'allow_shortage': False})
            case_dict.update({'max_shortage': 0})

        # activate stability constraint - here it is not optional!
        if 'stability_constraint' in case_dict:
            pass
        elif include_stability_constraint == True:
            case_dict.update({'stability_constraint': experiment['stability_limit']})
        else:
            case_dict.update({'stability_constraint': False})

        # not-optional renewable constraint
        if 'renewable_share_constraint' in case_dict:
            pass
        else:
            if experiment['min_renewable_share'] != 0:
                case_dict.update({'renewable_share_constraint': experiment['min_renewable_share']})
            else:
                case_dict.update({'renewable_share_constraint': False})

        case_dict.update({'evaluated_days': evaluated_days})

        return case_dict

    def model_and_simulate(experiment, case_dict, demand_profile, pv_generation_per_kWp, grid_availability):
        from config import output_folder, restore_oemof_if_existant

        file_name = oemof_model.filename(case_dict['case_name'], experiment['filename'])
        cases.extend_dictionary(case_dict, experiment, demand_profile)
        print(case_dict)

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
        oemof_results = evaluate_timeseries.get_all(case_dict, micro_grid_system, experiment, grid_availability,
                                                    max(pv_generation_per_kWp))
        return oemof_results

    def get_case_dict(name, experiment, demand_profile, capacities_base):
        from config import setting_batch_capacity

        if name == 'base_oem':
            ###############################################################################
            # Optimization of off-grid micro grid = Definition of base case capacities    #
            # Does not allow minimal loading of generator, but sizes it                   #
            ###############################################################################
            '''
            Case: micro grid with variable capacities = OEM

                            input/output    bus_fuel        bus_electricity
                                |               |               |
                                |               |               |
            source: pv          |------------------------------>|     var cap
                                |               |               |
            source: fossil_fuel |-------------->|               |
                                |               |               |
            trafo: generator    |<--------------|               |     var cap
                                |------------------------------>|
                                |               |               |
            storage: battery    |<------------------------------|     var cap
                                |------------------------------>|
                                |               |               |
            sink: demand        |<------------------------------|     fix
                                |               |               |
            sink: excess        |<------------------------------|     var
                                |               |               |
            sink: shortage      |<------------------------------|     var
                                |               |               |
            '''
            case_dict = {
                'case_name': 'base_oem',
                'pv_fixed_capacity': False,
                'storage_fixed_capacity': False,
                'genset_fixed_capacity': False,
                'pcc_consumption_fixed_capacity': None,
                'pcc_feedin_fixed_capacity': None,
                'stability_constraint': False
            }

        elif name == 'base_oem_with_min_loading':
            ###############################################################################
            # Optimization of off-grid micro grid = Definition of base case capacities    #
            # Allows minimal loading of generator with fixed capacity = peak demand       #
            ###############################################################################
            '''
            Case: micro grid with variable capacities = OEM

                            input/output    bus_fuel        bus_electricity
                                |               |               |
                                |               |               |
            source: pv          |------------------------------>|     var cap
                                |               |               |
            source: fossil_fuel |-------------->|               |
                                |               |               |
            trafo: generator    |<--------------|               |     var cap
                                |------------------------------>|
                                |               |               |
            storage: battery    |<------------------------------|     var cap
                                |------------------------------>|
                                |               |               |
            sink: demand        |<------------------------------|     fix
                                |               |               |
            sink: excess        |<------------------------------|     var
                                |               |               |
            sink: shortage      |<------------------------------|     var
                                |               |               |
            '''
            case_dict = {
                'case_name': 'base_oem_with_min_loading',
                'pv_fixed_capacity': False,
                'storage_fixed_capacity': False,
                'genset_fixed_capacity': max(demand_profile),
            # fix genset transformer, so that minimal loading can be used
                'pcc_consumption_fixed_capacity': None,
                'pcc_feedin_fixed_capacity': None,
            }


        elif name == 'offgrid_fixed':
            ###############################################################################
            #                Dispatch optimization with fixed capacities                  #
            ###############################################################################
            '''
            Case: micro grid with fixed capacities = dispatch analysis

                            input/output    bus_fuel        bus_electricity
                                |               |               |
                                |               |               |
            source: pv          |------------------------------>|     fix cap
                                |               |               |
            source: fossil_fuel |-------------->|               |
                                |               |               |
            trafo: generator    |<--------------|               |     fix cap
                                |------------------------------>|
                                |               |               |
            storage: battery    |<------------------------------|     fix cap
                                |------------------------------>|
                                |               |               |
            sink: demand        |<------------------------------|     fix
                                |               |               |
            sink: excess        |<------------------------------|     var
                                |               |               |
            sink: shortage      |<------------------------------|     var
                                |               |               |
            '''

            case_dict = {'case_name': 'offgrid_fixed'}

            if setting_batch_capacity == True:
                capacity_batch = oemof_process.process_oem_batch(capacities_base, case_dict['case_name'])

            case_dict.update({
                'pv_fixed_capacity': capacity_batch['capacity_pv_kWp'],
                'storage_fixed_capacity': capacity_batch['capacity_storage_kWh'],
                'genset_fixed_capacity': capacity_batch['capacity_genset_kW'],
                'pcc_consumption_fixed_capacity': None,
                'pcc_feedin_fixed_capacity': None,
                'allow_shortage': True,
                'max_shortage': 0.05
            })

        elif name == 'interconnected_buysell':
            ###########################################################################
            # Dispatch of off-grid micro grid interconnecting with national grid,     #
            # consumption and feed-in                                                 #
            ###########################################################################
            '''
            Case: 
            Micro grid connected to national grid, with point of common coupling allowing both consumption and
            feed-into grid. 

                            input/output    bus_fuel        bus_electricity      bus_electricity_ng
                                |               |               |                         |
                                |               |               |                         |
            source: pv          |------------------------------>|     fix cap             |
                                |               |               |                         |
            source: fossil_fuel |-------------->|               |                         |
                                |               |               |                         |
            trafo: generator    |<--------------|               |     fix cap             |
                                |------------------------------>|                         |
                                |               |               |                         |
            storage: battery    |<------------------------------|     fix cap             |
                                |------------------------------>|                         |
                                |               |               |                         |
            sink: demand        |<------------------------------|     fix                 |
                                |               |               |                         |
            sink: excess        |<------------------------------|     var                 |
                                |               |               |                         |
            sink: shortage      |<------------------------------|     var                 |
                                |               |               |                         |
            source: ng          |               |               |<------------------------| var
            sink: ng            |               |               |------------------------>|
            '''

            case_dict = {'case_name': 'interconnected_buysell'}

            capacities_base.update({"capacity_pcoupling_kW": max(demand_profile) / experiment['pcoupling_efficiency']})

            if setting_batch_capacity == True:
                capacity_batch = oemof_process.process_oem_batch(capacities_base, case_dict['case_name'])

            case_dict.update({
                'pv_fixed_capacity': capacity_batch['capacity_pv_kWp'],
                'storage_fixed_capacity': capacity_batch['capacity_storage_kWh'],
                'genset_fixed_capacity': capacity_batch['capacity_genset_kW'],
                'pcc_consumption_fixed_capacity': capacity_batch['capacity_pcoupling_kW'],
                'pcc_feedin_fixed_capacity': capacity_batch['capacity_pcoupling_kW']
            })

        elif name == 'interconnected_buy':
            ###########################################################################
            # Dispatch of off-grid micro grid interconnecting with national grid,     #
            # only consumption                                                        #
            ###########################################################################
            '''
            Case: 
            Micro grid connected to national grid, with point of common coupling allowing only consumption from grid. 

                            input/output    bus_fuel        bus_electricity      bus_electricity_ng
                                |               |               |                         |
                                |               |               |                         |
            source: pv          |------------------------------>|     fix cap             |
                                |               |               |                         |
            source: fossil_fuel |-------------->|               |                         |
                                |               |               |                         |
            trafo: generator    |<--------------|               |     fix cap             |
                                |------------------------------>|                         |
                                |               |               |                         |
            storage: battery    |<------------------------------|     fix cap             |
                                |------------------------------>|                         |
                                |               |               |                         |
            sink: demand        |<------------------------------|     fix                 |
                                |               |               |                         |
            sink: excess        |<------------------------------|     var                 |
                                |               |               |                         |
            sink: shortage      |<------------------------------|     var                 |
                                |               |               |                         |
            source: ng          |               |               |<------------------------| var
            '''

            case_dict = {'case_name': 'interconnected_buy'}

            capacities_base.update({"capacity_pcoupling_kW": max(demand_profile) / experiment['pcoupling_efficiency']})
            if setting_batch_capacity == True:
                capacity_batch = oemof_process.process_oem_batch(capacities_base, case_dict['case_name'])

            case_dict.update({
                'pv_fixed_capacity': capacity_batch['capacity_pv_kWp'],
                'storage_fixed_capacity': capacity_batch['capacity_storage_kWh'],
                'genset_fixed_capacity': capacity_batch['capacity_genset_kW'],
                'pcc_consumption_fixed_capacity': capacity_batch['capacity_pcoupling_kW'],
                'pcc_feedin_fixed_capacity': None
            })

        elif name == 'oem_grid_tied_mg':
            ###########################################################################
            # Optimal energy mix of grid-tied MG                                      #
            # = From the start interconnected with main grid                          #
            ###########################################################################
            '''
            Case: micro grid with variable capacities = OEM

                            input/output    bus_fuel        bus_electricity
                                |               |               |
                                |               |               |
            source: pv          |------------------------------>|     var cap
                                |               |               |
            source: fossil_fuel |-------------->|               |
                                |               |               |
            trafo: generator    |<--------------|               |     var cap
                                |------------------------------>|
                                |               |               |
            storage: battery    |<------------------------------|     var cap
                                |------------------------------>|
                                |               |               |
            sink: demand        |<------------------------------|     fix
                                |               |               |
            sink: excess        |<------------------------------|     var
                                |               |               |
            sink: shortage      |<------------------------------|     var
                                |               |               |
            source: ng          |               |               |<------------------------| var
            sink: ng            |               |               |------------------------>|
                    '''
            case_dict = {'case_name': 'oem_grid_tied_mg'}

            case_dict.update({
                'pv_fixed_capacity': False,
                'storage_fixed_capacity': False,
                'genset_fixed_capacity': False,
                'pcc_consumption_fixed_capacity': max(demand_profile) / experiment['pcoupling_efficiency'],
                'pcc_feedin_fixed_capacity': max(demand_profile) / experiment['pcoupling_efficiency']
            })

        elif name == 'sole_maingrid':
            '''
            Cost analysis of national grid supply, incl. LCOE

                            input/output  bus_electricity_mg  bus_electricity_ng
                                |               |               |
                                |               |               |

                                |               |               |
            sink: demand        |<--------------|     fix
                                |               |               |
            source: ng          |               |<--------------| var
            '''
            case_dict = {
                'case_name': 'sole_maingrid',
                'pv_fixed_capacity': None,
                'storage_fixed_capacity': None,
                'genset_fixed_capacity': None,
                'pcc_consumption_fixed_capacity': max(demand_profile) / experiment['pcoupling_efficiency'],
                'pcc_feedin_fixed_capacity': None,
                'allow_shortage': True,
                'max_shortage': 1,
                'stability_constraint': False,
                'renewable_share_constraint': False
            }

        else:
            logging.warning('Error! Case ' + name + ' does not exist!')

        return case_dict

################################ Not jet defined cases ################################################################

    ###############################################################################
    # Dispatch with MG as sunk costs
    ###############################################################################
    def buyoff():
        '''
        Case: Buyoff of micro grid with fixed capacities after x years = dispatch analysis for evaluation of costs p.a????

                        input/output    bus_fuel        bus_electricity
                            |               |               |
                            |               |               |
        source: pv          |------------------------------>|     fix cap
                            |               |               |
        source: fossil_fuel |-------------->|               |
                            |               |               |
        trafo: generator    |<--------------|               |     fix cap
                            |------------------------------>|
                            |               |               |
        storage: battery    |<------------------------------|     fix cap
                            |------------------------------>|
                            |               |               |
        sink: demand        |<------------------------------|     fix
                            |               |               |
        sink: excess        |<------------------------------|     var
                            |               |               |
        sink: shortage      |<------------------------------|     var
                            |               |               |
        '''
        return

    ###############################################################################
    # Dispatch at parallel operation (mg as backup)
    ###############################################################################
    def parallel():
        '''
        Case: micro grid parallel operation with grid extension ... how? another bus for grid electricity, and consumers
        or algorithms decide, which supply is chosen? or 50% of consumers stay with mg? or mg only provides during blackout times?

                        input/output    bus_fuel        bus_electricity
                            |               |               |
                            |               |               |
        source: pv          |------------------------------>|     fix cap
                            |               |               |
        source: fossil_fuel |-------------->|               |
                            |               |               |
        trafo: generator    |<--------------|               |     fix cap
                            |------------------------------>|
                            |               |               |
        storage: battery    |<------------------------------|     fix cap
                            |------------------------------>|
                            |               |               |
        sink: demand        |<------------------------------|     fix
                            |               |               |
        sink: excess        |<------------------------------|     var
                            |               |               |
        sink: shortage      |<------------------------------|     var
                            |               |               |
        '''
        return

    ###############################################################################
    # Dispatch with national grid as backup
    ###############################################################################
    def backupgrid():
        '''
        Case: micro grid with fixed capacities provides during blackout times

                        input/output    bus_fuel        bus_electricity
                            |               |               |
                            |               |               |
        source: pv          |------------------------------>|     fix cap
                            |               |               |
        source: fossil_fuel |-------------->|               |
                            |               |               |
        trafo: generator    |<--------------|               |     fix cap
                            |------------------------------>|
                            |               |               |
        storage: battery    |<------------------------------|     fix cap
                            |------------------------------>|
                            |               |               |
        sink: demand        |<------------------------------|     fix
                            |               |               |
        sink: excess        |<------------------------------|     var
                            |               |               |
        sink: shortage      |<------------------------------|     var
                            |               |               |
        '''
        return

    ###############################################################################
    # Optimal adapted MG design and dispatch
    ###############################################################################
    def adapted():
        '''
        Case: micro grid is optimized for additional cacities (lower capacities) with grid interconnection

                        input/output    bus_fuel        bus_electricity
                            |               |               |
                            |               |               |
        source: pv          |------------------------------>|     fix cap
                            |               |               |
        source: fossil_fuel |-------------->|               |
                            |               |               |
        trafo: generator    |<--------------|               |     fix cap
                            |------------------------------>|
                            |               |               |
        storage: battery    |<------------------------------|     fix cap
                            |------------------------------>|
                            |               |               |
        sink: demand        |<------------------------------|     fix
                            |               |               |
        sink: excess        |<------------------------------|     var
                            |               |               |
        sink: shortage      |<------------------------------|     var
                            |               |               |
        '''
        return


