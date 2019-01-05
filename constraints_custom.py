'''
For defining custom constraints of the micro grid solutions
'''
import pyomo.environ as po
import pprint as pp
import logging

def stability_criterion(model, case_dict, experiment, storage, sink_demand, genset, pcc_consumption, el_bus, grid_availability):
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

    case_dict: dictionary, includes
        'stability_constraint': float
                Share of demand that potentially has to be covered by genset/storage flows for stable operation
        'storage_fixed_capacity': False, float, None
        'genset_fixed_capacity': False, float, None

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

    stability_limit = case_dict['stability_constraint']
    ## ------- Get CAP_genset ------- #
    CAP_genset = 0
    if case_dict['genset_fixed_capacity'] != None:
        if case_dict['genset_fixed_capacity']==False:
            CAP_genset += model.InvestmentFlow.invest[genset, el_bus]
        elif isinstance(case_dict['genset_fixed_capacity'], float):
            CAP_genset += model.flows[genset, el_bus].nominal_value

    ## ------- Get CAP PCC ------- #
    cap_pcc = 0
    if case_dict['pcc_consumption_fixed_capacity'] != None:
        if case_dict['pcc_consumption_fixed_capacity'] == False:
            cap_pcc += model.InvestmentFlow.invest[pcc_consumption, el_bus]
        elif isinstance(case_dict['pcc_consumption_fixed_capacity'], float):
            cap_pcc += case_dict['pcc_consumption_fixed_capacity'] # todo: this didnt work - model.flows[pcc_consumption, el_bus].nominal_value

    def stability_rule(model, t):
        expr = CAP_genset
        ## ------- Get demand at t ------- #
        demand = model.flows[el_bus, sink_demand].actual_value[t] * model.flows[el_bus, sink_demand].nominal_value
        expr += - stability_limit * demand
        ##---------Grid consumption t-------#
        # this should not be actual consumption but possible one  - like grid_availability[t]*pcc_consumption_cap
        print(case_dict['pcc_consumption_fixed_capacity'])
        if case_dict['pcc_consumption_fixed_capacity'] != None:
            expr += cap_pcc * grid_availability[t]
            print(cap_pcc * grid_availability[t])
        ## ------- Get stored capacity storage at t------- #
        # todo adjust if timestep not 1 hr
        if case_dict['storage_fixed_capacity'] != None:
            storage_capacity = 0
            if case_dict['storage_fixed_capacity'] == False:  # Storage subject to OEM
                storage_capacity += model.GenericInvestmentStorageBlock.capacity[storage, t]
                expr += storage_capacity # todo well... this actually is not quite true. storage can only stem as much as its nominal value... model.flows[generic_storage, el_bus].actual_value ?
            elif isinstance(case_dict['storage_fixed_capacity'], float): # Fixed storage subject to dispatch
                storage_capacity += model.GenericStorageBlock.capacity[storage, t] # todo as above
            else:
                print ("Error: 'storage_fixed_capacity' can only be None, False or float.")
            expr += storage_capacity * experiment['storage_Crate_discharge']

        return (expr >= 0)

    model.stability_constraint = po.Constraint(model.TIMESTEPS, rule=stability_rule)

    return model

# todo add pcc consumption here
def stability_test(oemof_results, experiment, storage_capacity, demand_profile, genset_capacity):
    '''
    Testing simulation results for adherance to above defined stability criterion
    '''
    # todo adjust if timestep not 1 hr
    boolean_test = [
        genset_capacity + storage_capacity[t] * experiment['storage_Crate_discharge'] \
        >= experiment['stability_limit'] * demand_profile[t]
        for t in range(0, len(demand_profile.index))
    ]

    if all(boolean_test) == True:
        logging.debug("Stability criterion is fullfilled.")
    else:
        logging.warning("ATTENTION: Stability criterion NOT fullfilled!")
        oemof_results.update({'comments': oemof_results['comments'] + 'Stability criterion not fullfilled. '})

    return

def storage_criterion(case_dict, model, storage, el_bus, experiment):
    if storage == None:
        def discharge_rule(model, t):
            storage_capacity = 0
            if case_dict['storage_fixed_capacity'] == False:  # Storage subject to OEM
                storage_capacity += model.GenericInvestmentStorageBlock.capacity[storage, t]
            elif isinstance(case_dict['storage_fixed_capacity'], float): # Fixed storage subject to dispatch
                storage_capacity += model.GenericStorageBlock.capacity[storage, t]

            allowed_discharge = storage_capacity * experiment['storage_Crate_discharge']
            discharge = model.flow[storage, el_bus, t]

            return (discharge <= allowed_discharge)

        model.discharge_constraint = po.Constraint(model.TIMESTEPS, rule=discharge_rule)

        def charge_rule(model, t):
            storage_capacity = 0
            if case_dict['storage_fixed_capacity'] == False:  # Storage subject to OEM
                storage_capacity += model.GenericInvestmentStorageBlock.capacity[storage, t]
            elif isinstance(case_dict['storage_fixed_capacity'], int):  # Fixed storage subject to dispatch
                storage_capacity += model.GenericStorageBlock.capacity[storage, t]

            allowed_charge = storage_capacity * experiment['storage_Crate_charge']
            charge = model.flow[el_bus, storage, t]

            return (charge <= allowed_charge)

        model.charge_constraint = po.Constraint(model.TIMESTEPS, rule=charge_rule)

    return model

# todo implement renewable share criterion in oemof model and cases
def renewable_share_criterion(model, experiment, total_demand, genset, pcc_consumption, el_bus):
    # todo doesnt work
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

def renewable_share_test(oemof_results, experiment):
    '''
    Testing simulation results for adherance to above defined stability criterion
    '''
    boolean_test = (oemof_results['res_share'] >= experiment['min_renewable_share'])

    if boolean_test == False:
        logging.warning("ATTENTION: Minimal renewable share criterion NOT fullfilled!")
        oemof_results.update({'comments': oemof_results['comments'] + 'Renewable share criterion not fullfilled. '})
    else:
        logging.debug("Minimal renewable share is fullfilled.")

    return