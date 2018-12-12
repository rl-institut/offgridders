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
        CAP_genset += module.flows[genset, el_bus].nominal_capacity

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
        logging.info("ATTENTION: Stability criterion NOT fullfilled!")
    else:
        logging.info("Stability criterion is fullfilled.")

    return boolean_test