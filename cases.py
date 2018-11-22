'''
Overlying script for tool for the analysis of possible
operational modes of micro grids interconnecting with an unreliable national grid

Input from base case is capacity_base with keys 'storage_invest_kWh', 'pv_invest_kW', 'genset_invest_kW', 'res_share_perc'

'''

import os
import pandas



from oemof.tools import logger
import logging
# Logging
#logger.define_logging(logfile='main_tool.log',
#                      screen_level=logging.INFO,
#                      file_level=logging.DEBUG)

from oemof_generatemodel import generatemodel
from oemof_general import oemofmodel
from general_functions import extract

class cases():

    ###############################################################################
    # Optimization of off-grid micro grid = Definition of base case capacities    #
    ###############################################################################
    def base_oem(demand_profile, pv_generation, experiment):
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
        from config import allow_shortage
        case_name = "base_oem"
        micro_grid_system = oemofmodel.initialize_model()
        oemofmodel.textblock_oem()
        micro_grid_system, bus_fuel, bus_electricity_mg     = generatemodel.bus_basic(micro_grid_system)
        micro_grid_system, bus_fuel                         = generatemodel.fuel_oem(micro_grid_system, bus_fuel, extract.fuel(experiment), sum(demand_profile))
        if allow_shortage == True:
            micro_grid_system, bus_electricity_mg           = generatemodel.shortage(micro_grid_system, bus_electricity_mg, sum(demand_profile), extract.shortage(experiment))
        micro_grid_system, bus_electricity_mg               = generatemodel.demand(micro_grid_system, bus_electricity_mg, demand_profile)
        micro_grid_system, bus_electricity_mg               = generatemodel.excess(micro_grid_system, bus_electricity_mg)
        micro_grid_system, bus_electricity_mg               = generatemodel.pv_oem(micro_grid_system, bus_electricity_mg, pv_generation, extract.pv(experiment))
        micro_grid_system, bus_fuel, bus_electricity_mg     = generatemodel.genset_oem(micro_grid_system, bus_fuel, bus_electricity_mg, extract.genset(experiment))
        micro_grid_system, bus_electricity_mg               = generatemodel.storage_oem(micro_grid_system, bus_electricity_mg, extract.storage(experiment))
        micro_grid_system                                   = oemofmodel.simulate(micro_grid_system, case_name, experiment['filename'])
        oemofmodel.store_results(micro_grid_system, case_name, experiment['filename'])
        #micro_grid_system = oemofmodel.load_results() # todo not yet defined.
        oemof_results, capacities_base                             = oemofmodel.process_oem(micro_grid_system, case_name, max(pv_generation), extract.process_oem(experiment))

        print ("experiment['cost_annuity_pv']*capacities_base['pv_invest_kW']"+str(experiment['pv_cost_annuity']*capacities_base['pv_invest_kW']))
        print ("experiment['cost_annuity_genset']*capacities_base['genset_invest_kW']"+str(experiment['genset_cost_annuity']*capacities_base['genset_invest_kW']))
        print ("experiment['cost_annuity_storage'] * capacities_base['storage_invest_kWh']" + str(experiment['storage_cost_annuity'] * capacities_base['storage_invest_kWh']))

        #cases.draw(micro_grid_system)

        return oemof_results, capacities_base

    ###############################################################################
    #                Dispatch optimization with fixed capacities                  #
    ###############################################################################
    def mg_fix(demand_profile, pv_generation, experiment, capacity_base):
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
        from config import allow_shortage, setting_batch_capacity
        case_name = "mg_fix"
        if setting_batch_capacity == True:
            capacity_batch                                       = oemofmodel.process_oem_batch(capacity_base, case_name)
        micro_grid_system                                   = oemofmodel.initialize_model()
        oemofmodel.textblock_fix()
        micro_grid_system, bus_fuel, bus_electricity_mg     = generatemodel.bus_basic(micro_grid_system)
        micro_grid_system, bus_fuel                         = generatemodel.fuel_fix(micro_grid_system, bus_fuel, extract.fuel(experiment))
        if allow_shortage == True:
            micro_grid_system, bus_electricity_mg           = generatemodel.shortage(micro_grid_system, bus_electricity_mg, sum(demand_profile), extract.shortage(experiment))
        micro_grid_system, bus_electricity_mg               = generatemodel.demand(micro_grid_system, bus_electricity_mg, demand_profile)
        micro_grid_system, bus_electricity_mg               = generatemodel.excess(micro_grid_system, bus_electricity_mg)
        micro_grid_system, bus_electricity_mg               = generatemodel.pv_fix(micro_grid_system, bus_electricity_mg, pv_generation, capacity_batch['pv_invest_kW'], extract.pv(experiment))
        micro_grid_system, bus_fuel, bus_electricity_mg     = generatemodel.genset_fix(micro_grid_system, bus_fuel, bus_electricity_mg, capacity_batch['genset_invest_kW'], extract.genset(experiment))
        micro_grid_system, bus_electricity_mg               = generatemodel.storage_fix(micro_grid_system, bus_electricity_mg, capacity_batch['storage_invest_kWh'], extract.storage(experiment))
        micro_grid_system                                   = oemofmodel.simulate(micro_grid_system, case_name, experiment['filename'])
        oemofmodel.store_results(micro_grid_system, case_name, experiment['filename'])
        #micro_grid_system = oemofmodel.load_results()
        oemof_results = oemofmodel.process_fix(micro_grid_system, case_name, capacity_batch, extract.process_fix(experiment))
        return oemof_results

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
    # Dispatch at buy from and sell to grid
    ###############################################################################
    def buysell():
        '''
        Case: micro grid connected to national grid and can feed in and out at will
        only buy from grid, when chaper than own production??

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

    ###############################################################################
    # Optimal mix and dispatch at interconnected state
    ###############################################################################
    def oem_interconnected():
        '''
        Case: micro grid is optimized with grid interconnection

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

    def draw(energysystem):
        '''
        Compare with https://oemof.readthedocs.io/en/stable/api/oemof.html?highlight=graph#module-oemof.graph for additional settings
        '''
        import oemof.graph as graph
        import networkx as nx
        import matplotlib.pyplot as plt
        from config import output_folder

        energysystem_graph = graph.create_nx_graph(energysystem, filename=output_folder+'/'+'case_graph')

        return