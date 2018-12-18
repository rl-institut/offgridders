'''
For defining custom constraints of the micro grid solutions
'''
import pyomo.environ as po
import pprint as pp
import logging

def stability_criterion(model, stability_limit, storage, sink_demand, genset, el_bus):
    '''
    Set a minimal limit for operating reserve of diesel generator + storage to aid PV generation in case of volatilities
    = Ensure stability of MG system

      .. math:: for t in lp_files.TIMESTEPS:
            stability_limit * demand (t) <= CAP_genset + storage_capacity (t) *invest_relation_output_capacity

    Parameters
    - - - - - - - -

    model: oemof.solph.model
        Model to which constraint is added. Has to contain:
        - Sink for demand flow
        - Transformer (genset)
        - Storage (with invest_relation_output_capacity)

    stability_limit: float
        Share of demand that potentially has to be covered by genset/storage flows for stable operation

    storage: currently single object of class oemof.solph.components.GenericStorage
        To get stored capacity at t
        Has to include attibute invest_relation_output_capacity
        Can either be an investment object or have a nominal capacity

    sink_demand: currently single object of class oemof.solph.components.Sink
        To get demand at t

    genset: currently single object of class oemof.solph.network.Transformer
        To get available capacity genset
        Can either be an investment object or have a nominal capacity

    el_bus: object of class oemof.solph.network.Bus
        For accessing flow-parameters
    '''
    ## ------- Get CAP_genset ------- #
    CAP_genset = 0
    # genset capacity subject to oem
    if hasattr(model, "InvestmentFlow"):     # todo: not all generators have variable capacities, only because there are *any* investments optimized
        CAP_genset += model.InvestmentFlow.invest[genset, el_bus]
    # genset capacity subject to oem
    else:
        CAP_genset += model.flows[genset, el_bus].nominal_capacity

    def stability_rule(model, t):
        ## ------- Get demand at t ------- #
        demand = model.flow[el_bus,sink_demand,t]
        ## ------- Get stored capacity storage at t------- #
        storage_capacity = 0
        if hasattr(model, "InvestmentFlow"): # Storage subject to OEM
            storage_capacity += model.GenericInvestmentStorageBlock.capacity[storage, t]
        else: # Fixed storage subject to dispatch
            storage_capacity += model.GenericStorageBlock.capacity[storage, t]
        # todo adjust if timestep not 1 hr
        expr = CAP_genset + storage_capacity * storage.invest_relation_output_capacity\
               >= stability_limit * demand
        return expr

    model.stability_constraint = po.Constraint(model.TIMESTEPS, rule=stability_rule)

    return model

def stability_criterion_test(experiment, storage_capacity, demand_profile, genset_capacity):
    '''
    Testing simulation results for adherance to above defined stability criterion
    '''
    # todo adjust if timestep not 1 hr
    boolean_test = [
        genset_capacity + storage_capacity[t] * experiment['storage_Crate'] \
        >= experiment['stability_limit'] * demand_profile[t]
        for t in demand_profile.index]

    if any(boolean_test) == False:
        logging.WARNING("ATTENTION: Stability criterion NOT fullfilled!")
    else:
        logging.debug("Stability criterion is fullfilled.")

    return

# todo implement renewable share criterion in oemof model and cases
def renewable_share_criterion(model, experiment, total_demand, genset, pcc_consumption, el_bus):
    '''
    Resulting in an energy system adhering to a minimal renewable factor

      .. math::
            minimal renewable factor <= 1 - (fossil fuelled generation + main grid consumption * (1-main grid renewable factor)) / total_demand

    Parameters
    - - - - - - - -
    model: oemof.solph.model
        Model to which constraint is added. Has to contain:
        - Transformer (genset)
        - optional: pcc

    experiment: dict with entries...
        - 'min_res_share': Share of demand that can be met by fossil fuelled generation (genset, from main grid) to meet minimal renewable share
        - optional: 'main_grid_renewable_share': Share of main grid electricity that is generated renewably

    genset: currently single object of class oemof.solph.network.Transformer
        To get available capacity genset
        Can either be an investment object or have a nominal capacity

    pcc_consumption: currently single object of class oemof.solph.network.Transformer
        Connecting main grid bus to electricity bus of micro grid (consumption)

    el_bus: object of class oemof.solph.network.Bus
        For accessing flow-parameters
    '''

    #print("1")
    #print (model.flow[genset, el_bus, 0])
    #print (dir(model.flow[genset, el_bus, 0]))
    #print("2")
    #sum = 0
    #for t in model.TIMESTEPS:
    #    sum +=model.flow[genset, el_bus, t]
    #print(sum)
    #print("3")
    #print(model.flow[genset, el_bus])
    def renewable_share_rule(model):
        # generation of fossil-fuelled generator
        actual_fossil_generation = sum(model.flow[genset, el_bus, t] for t in model.TIMESTEPS)
        # consumption from grid, if connected
        if pcc_consumption != None:
            actual_fossil_generation += sum(model.flow[pcc_consumption, el_bus, t] for t in model.TIMESTEPS) \
                                        * (1 - experiment['maingrid_renewable_share'])

        expr = (experiment['min_renewable_share'] <= 1 - actual_fossil_generation/total_demand)
        return expr


    model.renewable_share_constraint = po.Constraint(rule=renewable_share_rule)

    return model

def renewable_share_test(experiment, total_demand, total_generation_genset, total_main_grid_consumption):
    '''
    Testing simulation results for adherance to above defined stability criterion
    '''
    # todo adjust if timestep not 1 hr

    actual_fossil_generation = total_generation_genset
    if total_main_grid_consumption != None:
        actual_fossil_generation += (1-experiment['maingrid_renewable_share']) * total_main_grid_consumption

    boolean_test = (total_demand * (1-experiment['min_renewable_share']) >= actual_fossil_generation)

    if boolean_test == False:
        logging.WARNING("ATTENTION: Minimal renewable share criterion NOT fullfilled!")
    else:
        logging.DEBUG("Minimal renewable share is fullfilled.")

    return