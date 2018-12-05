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

# For speeding up model and bus/component definition in oemof as well as processing
from oemof_generatemodel import generatemodel
from oemof_general import oemofmodel

# This is not really a necessary class, as the whole experiement could be given to the function, but it ensures, that
# only correct input data is included

class cases():
    ###############################################################################
    # Optimization of off-grid micro grid = Definition of base case capacities    #
    # Does not allow minimal loading of generator, but sizes it                   #
    ###############################################################################
    def base_oem(demand_profile, pv_generation, experiment):
        from config import output_folder, restore_oemof_if_existant, allow_shortage
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
        case_name = "base_oem"
        file_name = oemofmodel.filename(case_name, experiment['filename'])

        # For restoring .oemof results if that is possible (speeding up computation time)
        if os.path.isfile(output_folder + "/oemof/" + file_name + ".oemof") and restore_oemof_if_existant == True:
            logging.info("Previous results of " + case_name + " restored.")

        # If .oemof results do not already exist, start oemof-process
        else:
            total_demand    = sum(demand_profile)
            # creating energysystem with date-time-frame
            micro_grid_system = oemofmodel.initialize_model()
            oemofmodel.textblock_oem()
            # add bus (fuel, electricity_mg)
            micro_grid_system, bus_fuel, bus_electricity_mg     = generatemodel.bus_basic(micro_grid_system)
            # add fuel source
            micro_grid_system, bus_fuel                         = generatemodel.fuel_oem(micro_grid_system, bus_fuel, experiment, total_demand)
            if allow_shortage == True:
                # add source shortage, if allowed
                micro_grid_system, bus_electricity_mg           = generatemodel.shortage(micro_grid_system, bus_electricity_mg, total_demand, experiment)
            # add demand sink
            micro_grid_system, bus_electricity_mg               = generatemodel.demand(micro_grid_system, bus_electricity_mg, demand_profile)
            # add excess sink
            micro_grid_system, bus_electricity_mg               = generatemodel.excess(micro_grid_system, bus_electricity_mg)
            # add pv source
            micro_grid_system, bus_electricity_mg               = generatemodel.pv_oem(micro_grid_system, bus_electricity_mg, pv_generation, experiment)
            # add genset transformer
            micro_grid_system, bus_fuel, bus_electricity_mg     = generatemodel.genset_oem(micro_grid_system, bus_fuel, bus_electricity_mg, experiment)
            # add storage
            micro_grid_system, bus_electricity_mg               = generatemodel.storage_oem(micro_grid_system, bus_electricity_mg, experiment)
            # perform simulation
            micro_grid_system                                   = oemofmodel.simulate(micro_grid_system, file_name)
            # store simulation results to .oemof
            oemofmodel.store_results(micro_grid_system, file_name)

        # load oemof results from previous or just finished simulation
        micro_grid_system = oemofmodel.load_oemof_results(file_name)

        # process results
        oemof_results, capacities_base                             = oemofmodel.process_oem(micro_grid_system, case_name, max(pv_generation), experiment, demand_profile)

        # todo: better graph for created energysystems if NO outputfolder/outputfile_casename* exist!
        #oemofmodel.draw(micro_grid_system)

        return oemof_results, capacities_base

    ###############################################################################
    # Optimization of off-grid micro grid = Definition of base case capacities    #
    # Allows minimal loading of generator with fixed capacity = peak demand       #
    ###############################################################################
    def base_oem_min_loading(demand_profile, pv_generation, experiment):
        from config import output_folder, restore_oemof_if_existant, allow_shortage
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
        case_name = "base_oem_with_min_loading"
        file_name = oemofmodel.filename(case_name, experiment['filename'])

        # For restoring .oemof results if that is possible (speeding up computation time)
        if os.path.isfile(output_folder + "/oemof/" + file_name + ".oemof") and restore_oemof_if_existant == True:
            logging.info("Previous results of " + case_name + " restored.")

        # If .oemof results do not already exist, start oemof-process
        else:
            total_demand    = sum(demand_profile)
            peak_demand     = max(demand_profile)
            # creating energysystem with date-time-frame
            micro_grid_system = oemofmodel.initialize_model()
            oemofmodel.textblock_oem()
            # add bus (fuel, electricity_mg)
            micro_grid_system, bus_fuel, bus_electricity_mg     \
                = generatemodel.bus_basic(micro_grid_system)
            # add fuel source
            micro_grid_system, bus_fuel                         \
                = generatemodel.fuel_oem(micro_grid_system, bus_fuel, experiment, total_demand)
            if allow_shortage == True:
                # add source shortage, if allowed
                micro_grid_system, bus_electricity_mg           \
                    = generatemodel.shortage(micro_grid_system, bus_electricity_mg, total_demand, experiment)
            # add demand sink
            micro_grid_system, bus_electricity_mg               \
                = generatemodel.demand(micro_grid_system, bus_electricity_mg, demand_profile)
            # add excess sink
            micro_grid_system, bus_electricity_mg               \
                = generatemodel.excess(micro_grid_system, bus_electricity_mg)
            # add pv source
            micro_grid_system, bus_electricity_mg               \
                = generatemodel.pv_oem(micro_grid_system, bus_electricity_mg, pv_generation, experiment)
            # add genset transformer (fix, with minimal loading)
            micro_grid_system, bus_fuel, bus_electricity_mg     \
                = generatemodel.genset_fix(micro_grid_system, bus_fuel, bus_electricity_mg, peak_demand, experiment)
            # add storage
            micro_grid_system, bus_electricity_mg               \
                = generatemodel.storage_oem(micro_grid_system, bus_electricity_mg, experiment)
            # perform simulation
            micro_grid_system                                   \
                = oemofmodel.simulate(micro_grid_system, file_name)
            # store simulation results to .oemof
            oemofmodel.store_results(micro_grid_system, file_name)

        # load oemof results from previous or just finished simulation
        micro_grid_system = oemofmodel.load_oemof_results(file_name)

        # process results
        oemof_results, capacities_base                             \
            = oemofmodel.process_oem(micro_grid_system, case_name, max(pv_generation), experiment, demand_profile)

        # todo: better graph for created energysystems if NO outputfolder/outputfile_casename* exist!
        #oemofmodel.draw(micro_grid_system)

        return oemof_results, capacities_base

    ###############################################################################
    #                Dispatch optimization with fixed capacities                  #
    ###############################################################################
    def offgrid_fix(demand_profile, pv_generation, experiment, capacity_base):
        from config import output_folder, restore_oemof_if_existant, allow_shortage, setting_batch_capacity
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
        case_name = "offgrid_fix"
        file_name = oemofmodel.filename(case_name, experiment['filename'])
        if setting_batch_capacity == True:
            capacity_batch = oemofmodel.process_oem_batch(capacity_base, case_name)

        if os.path.isfile(output_folder + "/oemof/" + file_name + ".oemof") and restore_oemof_if_existant == True:
            logging.info("Previous results of " + case_name + " restored. \n Attention! If changed, batch capacities might be different!")
        else:
            total_demand                                        = sum(demand_profile)
            micro_grid_system                                   = oemofmodel.initialize_model()
            oemofmodel.textblock_fix()
            micro_grid_system, bus_fuel, bus_electricity_mg     = generatemodel.bus_basic(micro_grid_system)
            micro_grid_system, bus_fuel                         = generatemodel.fuel_fix(micro_grid_system, bus_fuel, experiment)
            if allow_shortage == True:
                micro_grid_system, bus_electricity_mg           \
                    = generatemodel.shortage(micro_grid_system, bus_electricity_mg, total_demand, experiment)
            micro_grid_system, bus_electricity_mg               \
                = generatemodel.demand(micro_grid_system, bus_electricity_mg, demand_profile)
            micro_grid_system, bus_electricity_mg               = generatemodel.excess(micro_grid_system, bus_electricity_mg)
            micro_grid_system, bus_electricity_mg               \
                = generatemodel.pv_fix(micro_grid_system, bus_electricity_mg, pv_generation, capacity_batch['pv_capacity_kW'], experiment)
            micro_grid_system, bus_fuel, bus_electricity_mg     \
                = generatemodel.genset_fix(micro_grid_system, bus_fuel, bus_electricity_mg, capacity_batch['genset_capacity_kW'], experiment)
            micro_grid_system, bus_electricity_mg               \
                = generatemodel.storage_fix(micro_grid_system, bus_electricity_mg, capacity_batch['storage_capacity_kWh'], experiment)
            micro_grid_system                                   = oemofmodel.simulate(micro_grid_system, file_name)
            oemofmodel.store_results(micro_grid_system, file_name)

        micro_grid_system = oemofmodel.load_oemof_results(file_name)
        oemof_results \
            = oemofmodel.process_fix(micro_grid_system, case_name, capacity_batch, experiment, demand_profile)

        return oemof_results

    ###########################################################################
    # Dispatch of off-grid micro grid interconnecting with national grid,     #
    # consumption and feed-in                                                 #
    ###########################################################################
    def interconnected_buysell(demand_profile, pv_generation, experiment, capacity_base, grid_availability):
        from config import output_folder, restore_oemof_if_existant, allow_shortage, setting_batch_capacity
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
        case_name = "interconnected_buysell"
        file_name = oemofmodel.filename(case_name, experiment['filename'])
        capacity_base.update({"capacity_pcoupling_kW": max(demand_profile)})
        if setting_batch_capacity == True:
            capacity_batch = oemofmodel.process_oem_batch(capacity_base, case_name)

        if os.path.isfile(output_folder + "/oemof/" + file_name + ".oemof") and restore_oemof_if_existant == True:
            logging.info("Previous results of " + case_name + " restored. \n Attention! If changed, batch capacities might be different!")
        else:
            total_demand    = sum(demand_profile)
            micro_grid_system                                   = oemofmodel.initialize_model()
            oemofmodel.textblock_fix()
            micro_grid_system, bus_fuel, bus_electricity_mg     = generatemodel.bus_basic(micro_grid_system)
            micro_grid_system, bus_fuel                         \
                = generatemodel.fuel_fix(micro_grid_system, bus_fuel, experiment)
            if allow_shortage == True:
                micro_grid_system, bus_electricity_mg           \
                    = generatemodel.shortage(micro_grid_system, bus_electricity_mg, total_demand, experiment)
            micro_grid_system, bus_electricity_mg               \
                = generatemodel.demand(micro_grid_system, bus_electricity_mg, demand_profile)
            micro_grid_system, bus_electricity_mg               = generatemodel.excess(micro_grid_system, bus_electricity_mg)
            micro_grid_system, bus_electricity_mg               \
                = generatemodel.pv_fix(micro_grid_system, bus_electricity_mg, pv_generation, capacity_batch['capacity_pv_kWp'], experiment)
            micro_grid_system, bus_fuel, bus_electricity_mg     \
                = generatemodel.genset_fix(micro_grid_system, bus_fuel, bus_electricity_mg, capacity_batch['capacity_genset_kW'], experiment)
            micro_grid_system, bus_electricity_mg               \
                = generatemodel.storage_fix(micro_grid_system, bus_electricity_mg, capacity_batch['capacity_storage_kWh'], experiment)
            # Additional for specific case:
            # Include national grid electricity bus
            micro_grid_system, bus_electricity_ng               = generatemodel.bus_el_ng(micro_grid_system)
            # Include national grid source (for consumption)
            micro_grid_system, bus_electricity_ng                         \
                = generatemodel.maingrid_consumption(micro_grid_system, bus_electricity_ng, experiment, grid_availability)
            # include national grid sink (for feed-in)
            micro_grid_system, bus_electricity_ng                         \
                = generatemodel.maingrid_feedin(micro_grid_system, bus_electricity_ng, experiment, grid_availability)
            # include point of common coupling (main grid -> micro grid)
            micro_grid_system, bus_electricity_mg, bus_electricity_ng \
                = generatemodel.pointofcoupling_consumption_fix(micro_grid_system, bus_electricity_mg, bus_electricity_ng,
                                                                capacity_batch["capacity_pcoupling_kW"], experiment)
            # include point of common coupling (micro grid -> main grid)
            micro_grid_system, bus_electricity_mg, bus_electricity_ng \
                = generatemodel.pointofcoupling_feedin_fix(micro_grid_system, bus_electricity_mg, bus_electricity_ng,
                                                           capacity_batch["capacity_pcoupling_kW"], experiment)

            micro_grid_system                                   = oemofmodel.simulate(micro_grid_system, file_name)
            oemofmodel.store_results(micro_grid_system, file_name)

        micro_grid_system = oemofmodel.load_oemof_results(file_name)

        oemof_results \
            = oemofmodel.process_fix(micro_grid_system, case_name, capacity_batch, experiment, demand_profile)

        return oemof_results

    ###########################################################################
    # Dispatch of off-grid micro grid interconnecting with national grid,     #
    # only consumption                                                        #
    ###########################################################################
    def interconnected_buy(demand_profile, pv_generation, experiment, capacity_base, grid_availability):
        from config import output_folder, restore_oemof_if_existant, allow_shortage, setting_batch_capacity
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
        case_name = "interconnected_buy"
        file_name = oemofmodel.filename(case_name, experiment['filename'])
        capacity_base.update({"capacity_pcoupling_kW": max(demand_profile)})
        if setting_batch_capacity == True:
            capacity_batch = oemofmodel.process_oem_batch(capacity_base, case_name)

        if os.path.isfile(output_folder + "/oemof/" + file_name + ".oemof") and restore_oemof_if_existant == True:
            logging.info("Previous results of " + case_name + " restored. \n Attention! If changed, batch capacities might be different!")
        else:
            total_demand = sum(demand_profile)
            micro_grid_system = oemofmodel.initialize_model()
            oemofmodel.textblock_fix()
            micro_grid_system, bus_fuel, bus_electricity_mg = generatemodel.bus_basic(micro_grid_system)
            micro_grid_system, bus_fuel \
                = generatemodel.fuel_fix(micro_grid_system, bus_fuel, experiment)
            if allow_shortage == True:
                micro_grid_system, bus_electricity_mg \
                    = generatemodel.shortage(micro_grid_system, bus_electricity_mg, total_demand, experiment)
            micro_grid_system, bus_electricity_mg \
                = generatemodel.demand(micro_grid_system, bus_electricity_mg, demand_profile)
            micro_grid_system, bus_electricity_mg = generatemodel.excess(micro_grid_system, bus_electricity_mg)
            micro_grid_system, bus_electricity_mg \
                = generatemodel.pv_fix(micro_grid_system, bus_electricity_mg, pv_generation,
                                       capacity_batch['capacity_pv_kWp'], experiment)
            micro_grid_system, bus_fuel, bus_electricity_mg \
                = generatemodel.genset_fix(micro_grid_system, bus_fuel, bus_electricity_mg,
                                           capacity_batch['capacity_genset_kW'], experiment)
            micro_grid_system, bus_electricity_mg \
                = generatemodel.storage_fix(micro_grid_system, bus_electricity_mg,
                                            capacity_batch['capacity_storage_kWh'], experiment)
            # Additional for specific case:
            # Include national grid electricity bus
            micro_grid_system, bus_electricity_ng = generatemodel.bus_el_ng(micro_grid_system)
            # Include national grid source (for consumption)
            micro_grid_system, bus_electricity_ng \
                = generatemodel.maingrid_consumption(micro_grid_system, bus_electricity_ng, experiment,
                                                     grid_availability)
            # include national grid sink (for feed-in)
            micro_grid_system, bus_electricity_ng \
                = generatemodel.maingrid_feedin(micro_grid_system, bus_electricity_ng, experiment, grid_availability)
            # include point of common coupling (main grid -> micro grid)
            micro_grid_system, bus_electricity_mg, bus_electricity_ng \
                = generatemodel.pointofcoupling_consumption_fix(micro_grid_system, bus_electricity_mg,
                                                                bus_electricity_ng,
                                                                capacity_batch["capacity_pcoupling_kW"], experiment)
            # include point of common coupling (micro grid -> main grid)
            micro_grid_system, bus_electricity_mg, bus_electricity_ng \
                = generatemodel.pointofcoupling_feedin_fix(micro_grid_system, bus_electricity_mg, bus_electricity_ng,
                                                           capacity_batch["capacity_pcoupling_kW"], experiment)

            micro_grid_system = oemofmodel.simulate(micro_grid_system, file_name)
            oemofmodel.store_results(micro_grid_system, file_name)

        micro_grid_system = oemofmodel.load_oemof_results(file_name)

        oemof_results \
            = oemofmodel.process_fix(micro_grid_system, case_name, capacity_batch, experiment, demand_profile)

        return oemof_results

    ###########################################################################
    # Optimal energy mix of grid-tied MG                                      #
    # = From the start interconnected with main grid                          #
    ###########################################################################
    def oem_grid_tied_mg(demand_profile, pv_generation, experiment, grid_availability):
        from config import output_folder, restore_oemof_if_existant, allow_shortage
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
        case_name = "oem_grid_tied_mg"
        file_name = oemofmodel.filename(case_name, experiment['filename'])

        # For restoring .oemof results if that is possible (speeding up computation time)
        if os.path.isfile(output_folder + "/oemof/" + file_name + ".oemof") and restore_oemof_if_existant == True:
            logging.info("Previous results of " + case_name + " restored.")

        # If .oemof results do not already exist, start oemof-process
        else:
            total_demand    = sum(demand_profile)
            peak_demand     = max(demand_profile)
            # creating energysystem with date-time-frame
            micro_grid_system = oemofmodel.initialize_model()
            oemofmodel.textblock_oem()
            # add bus (fuel, electricity_mg)
            micro_grid_system, bus_fuel, bus_electricity_mg     = generatemodel.bus_basic(micro_grid_system)
            # add fuel source
            micro_grid_system, bus_fuel                         = generatemodel.fuel_oem(micro_grid_system, bus_fuel, experiment, total_demand)
            if allow_shortage == True:
                # add source shortage, if allowed
                micro_grid_system, bus_electricity_mg           = generatemodel.shortage(micro_grid_system, bus_electricity_mg, total_demand, experiment)
            # add demand sink
            micro_grid_system, bus_electricity_mg               = generatemodel.demand(micro_grid_system, bus_electricity_mg, demand_profile)
            # add excess sink
            micro_grid_system, bus_electricity_mg               = generatemodel.excess(micro_grid_system, bus_electricity_mg)
            # add pv source
            micro_grid_system, bus_electricity_mg               = generatemodel.pv_oem(micro_grid_system, bus_electricity_mg, pv_generation, experiment)
            # add genset transformer
            micro_grid_system, bus_fuel, bus_electricity_mg     = generatemodel.genset_oem(micro_grid_system, bus_fuel, bus_electricity_mg, experiment)
            # add storage
            micro_grid_system, bus_electricity_mg               = generatemodel.storage_oem(micro_grid_system, bus_electricity_mg, experiment)

            # Additional for specific case:
            # Include national grid electricity bus
            micro_grid_system, bus_electricity_ng = generatemodel.bus_el_ng(micro_grid_system)
            # Include national grid source (for consumption)
            micro_grid_system, bus_electricity_ng \
                = generatemodel.maingrid_consumption(micro_grid_system, bus_electricity_ng, experiment,
                                                     grid_availability)
            # include national grid sink (for feed-in)
            micro_grid_system, bus_electricity_ng \
                = generatemodel.maingrid_feedin(micro_grid_system, bus_electricity_ng, experiment, grid_availability)
            # include point of common coupling (main grid -> micro grid)
            micro_grid_system, bus_electricity_mg, bus_electricity_ng \
                = generatemodel.pointofcoupling_consumption_fix(micro_grid_system, bus_electricity_mg,
                                                                bus_electricity_ng, peak_demand, experiment)
            # include point of common coupling (micro grid -> main grid)
            micro_grid_system, bus_electricity_mg, bus_electricity_ng \
                = generatemodel.pointofcoupling_feedin_fix(micro_grid_system, bus_electricity_mg, bus_electricity_ng,
                                                           peak_demand, experiment)

            # perform simulation
            micro_grid_system                                   = oemofmodel.simulate(micro_grid_system, file_name)
            # store simulation results to .oemof
            oemofmodel.store_results(micro_grid_system, file_name)

        # load oemof results from previous or just finished simulation
        micro_grid_system = oemofmodel.load_oemof_results(file_name)

        # process results
        oemof_results, capacities_base                            \
            = oemofmodel.process_oem(micro_grid_system, case_name, max(pv_generation), experiment, demand_profile)

        # todo: better graph for created energysystems if NO outputfolder/outputfile_casename* exist!
        #oemofmodel.draw(micro_grid_system)

        return oemof_results

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


