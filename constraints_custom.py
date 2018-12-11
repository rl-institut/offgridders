'''
For defining custom constraints of the micro grid solutions
'''
import pyomo.environ as po

import pprint as pp
from oemof.solph.options import Investment
import oemof

def stability_criterion(model, stability_limit, storage, sink_demand, genset, el_bus):
    '''
    Set a minimal limit for operating reserve of diesel generator + storage to aid PV generation in case of volatilities
    = Ensure stability of MG system

      .. math:: for t in lp_files.TIMESTEPS:
            stability_limit * demand (t) <= CAP_genset + storage_capacity (t) *invest_relation_output_capacity

    Parameters
    - - - - - - - -

    lp_files: oemof.solph.lp_files
        Model to which constraint is added. Has to contain:
        - Sink for demand flow
        - Transformer (genset)
        - Storage (with invest_relation_output_capacity)

    stability_limit: float
        Share of demand that potentially has to be covered by genset/storage flows for stable operation
    '''
    ## ------- Get CAP_genset ------- #

    CAP_genset = 0
    CAP_genset_pcc = 0

    # If oem, take generator capacities from variable invest
    if hasattr(model, "InvestmentFlow"):
        for i,o in model.InvestmentFlow.invest:
            # This loop only adds the genset to the potential generation
            if str(i)=='transformer_fuel_generator' and str(o)=='bus_electricity_mg':
                if isinstance(model.InvestmentFlow.invest[i, o].value, int):
                    CAP_genset += model.InvestmentFlow.invest[i, o].value

            # This loop adds the genset as well as pcc capacities to potential generation
            if isinstance(i, oemof.solph.network.Transformer) and str(o)=='bus_electricity_mg':
                if isinstance(model.InvestmentFlow.invest[i, o].value, int):
                    CAP_genset_pcc += model.InvestmentFlow.invest[i,o].value
    # If dispatch, take generator capacities from nominal_capacity
    else:
        for i, o in model.Flows:
            if str(i) == 'transformer_fuel_generator' and str(o) == 'bus_electricity_mg':
                CAP_genset = module.flows[i,o].nominal_capacity
            # This loop adds the genset as well as pcc capacities to potential generation
            if isinstance(i, oemof.solph.network.Transformer) and str(o)=='bus_electricity_mg':
                if isinstance(model.InvestmentFlow.invest[i, o].value, int):
                    CAP_genset_pcc += module.flows[i,o].nominal_capacity

    def stability_rule(model, t):
        # get demand at t
        demand = model.flow[el_bus,sink_demand,t]
        # get storage_capacity at t
        storage_capacity = model.GenericInvestmentStorageBlock.capacity[storage, t]
        print(CAP_genset, storage_capacity, demand)
        print (CAP_genset + storage_capacity * storage.invest_relation_output_capacity >= stability_limit * demand)
        return CAP_genset + storage_capacity * storage.invest_relation_output_capacity >= stability_limit * demand

    model.stability_criterion = po.Constraint(model.TIMESTEPS, rule=stability_rule)

    return model