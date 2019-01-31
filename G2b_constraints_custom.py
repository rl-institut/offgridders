'''
For defining custom constraints of the micro grid solutions
'''
import pyomo.environ as po
import pprint as pp
import logging
import pandas as pd

def stability_criterion(model, case_dict, experiment, storage, sink_demand, genset, pcc_consumption, source_shortage, el_bus):
    '''
    Set a minimal limit for operating reserve of diesel generator + storage to aid PV generation in case of volatilities
    = Ensure stability of MG system

      .. math:: for t in lp_files.TIMESTEPS:
            stability_limit * demand (t) <= CAP_genset + stored_electricity (t) *invest_relation_output_capacity

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
    ## ------- Get CAP genset ------- #
    CAP_genset = 0
    if case_dict['genset_fixed_capacity'] != None:
        if case_dict['genset_fixed_capacity']==False:
            CAP_genset += model.InvestmentFlow.invest[genset, el_bus]
        elif isinstance(case_dict['genset_fixed_capacity'], float):
            CAP_genset += model.flows[genset, el_bus].nominal_value

    ## ------- Get CAP PCC ------- #
    CAP_pcc = 0
    if case_dict['pcc_consumption_fixed_capacity'] != None:
        if case_dict['pcc_consumption_fixed_capacity'] == False:
            CAP_pcc += model.InvestmentFlow.invest[pcc_consumption, el_bus]
        elif isinstance(case_dict['pcc_consumption_fixed_capacity'], float):
            CAP_pcc += case_dict['pcc_consumption_fixed_capacity'] # todo: this didnt work - model.flows[pcc_consumption, el_bus].nominal_value

    def stability_rule(model, t):
        expr = CAP_genset
        ## ------- Get demand at t ------- #
        demand = model.flows[el_bus, sink_demand].actual_value[t] * model.flows[el_bus, sink_demand].nominal_value
        expr += - stability_limit * demand
        ## ------- Get shortage at t------- #
        if case_dict['allow_shortage'] == True:
            shortage = model.flow[source_shortage,el_bus,t]
            expr += - stability_limit * shortage
        ##---------Grid consumption t-------#
        # this should not be actual consumption but possible one  - like grid_availability[t]*pcc_consumption_cap
        if case_dict['pcc_consumption_fixed_capacity'] != None:
            expr += CAP_pcc * experiment['grid_availability'][t]

        ## ------- Get stored capacity storage at t------- #
        # todo adjust if timestep not 1 hr
        if case_dict['storage_fixed_capacity'] != None:
            stored_electricity = 0
            if case_dict['storage_fixed_capacity'] == False:  # Storage subject to OEM
                stored_electricity += model.GenericInvestmentStorageBlock.capacity[storage, t]  - experiment['storage_capacity_min'] * model.GenericInvestmentStorageBlock.invest[storage]
            elif isinstance(case_dict['storage_fixed_capacity'], float): # Fixed storage subject to dispatch
                stored_electricity += model.GenericStorageBlock.capacity[storage, t] - experiment['storage_capacity_min'] * storage.nominal_capacity
            else:
                print ("Error: 'storage_fixed_capacity' can only be None, False or float.")
            expr += stored_electricity * experiment['storage_Crate_discharge']
        return (expr >= 0)

    model.stability_constraint = po.Constraint(model.TIMESTEPS, rule=stability_rule)

    return model

# todo add pcc consumption here
def stability_test(case_dict, oemof_results, experiment, e_flows_df):
    '''
        Testing simulation results for adherance to above defined stability criterion
    '''
    if case_dict['stability_constraint']!=False:
        demand_profile = e_flows_df['Demand']

        if ('Stored capacity' in e_flows_df.columns):
            stored_electricity = e_flows_df['Stored capacity']
        else:
            stored_electricity = pd.Series([0 for t in demand_profile.index], index=demand_profile.index)

        if ('Grid availability' in e_flows_df.columns):
            pcc_capacity = oemof_results['capacity_pcoupling_kW'] * e_flows_df['Grid availability']
        else:
            pcc_capacity = pd.Series([0 for t in demand_profile.index], index=demand_profile.index)

        genset_capacity = oemof_results['capacity_genset_kW']

        if case_dict['allow_shortage'] == True:
            shortage = e_flows_df['Demand shortage']
        else:
            shortage = pd.Series([0 for t in demand_profile.index], index=demand_profile.index)

        # todo adjust if timestep not 1 hr
        boolean_test = [
            genset_capacity
            + (stored_electricity[t] - oemof_results['capacity_storage_kWh'] *  experiment['storage_capacity_min']) *  experiment['storage_Crate_discharge']
            + pcc_capacity[t] \
            >= experiment['stability_limit'] * (demand_profile[t] - shortage[t])
            for t in range(0, len(demand_profile.index))
            ]

        if all(boolean_test) == True:
            logging.debug("Stability criterion is fullfilled.")
        else:
            logging.warning("ATTENTION: Stability criterion NOT fullfilled!")
            logging.warning('Number of timesteps not meeting criteria: ' + str(sum(boolean_test)))
            ratio = pd.Series([
                (genset_capacity + (stored_electricity[t] - oemof_results['capacity_storage_kWh'] * experiment['storage_capacity_min']) *
                experiment['storage_Crate_discharge'] + pcc_capacity[t] - experiment['stability_limit'] * (demand_profile[t] - shortage[t]))
                / (experiment['peak_demand'])
                for t in range(0, len(demand_profile.index))], index=demand_profile.index)
            ratio_below_zero=ratio.clip_upper(0)
            logging.warning('Deviation from stability criterion: '+ str(ratio_below_zero.values.mean()) + '(mean) / '+ str(ratio_below_zero.values.min()) + '(max).')
            oemof_results.update({'comments': oemof_results['comments'] + 'Stability criterion not fullfilled (max deviation '+ str(round(100*ratio_below_zero.values.min(), 4)) + '%). '})
    else:
        pass

    return

# todo implement renewable share criterion in oemof model and cases
def renewable_share_criterion(model, experiment, genset, pcc_consumption, solar_plant, el_bus): #wind_plant
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

    def renewable_share_rule(model):
        fossil_generation = 0
        total_generation = 0

        if genset is not None:
            genset_generation_kWh = sum(model.flow[genset, el_bus, t] for t in model.TIMESTEPS)
            print(genset_generation_kWh)
            total_generation += genset_generation_kWh
            fossil_generation += genset_generation_kWh

        if pcc_consumption is not None:
            pcc_consumption_kWh = sum(model.flow[pcc_consumption, el_bus, t] for t in model.TIMESTEPS)
            print(pcc_consumption_kWh)
            total_generation += pcc_consumption
            fossil_generation += pcc_consumption_kWh * (1 - experiment['maingrid_renewable_share'])

        #if wind_plant != None:
        #    wind_plant_generation_kWh = sum(model.flow[wind_plant, el_bus, t] for t in model.TIMESTEPS)
        #    total_generation += wind_plant_generation_kWh

        if solar_plant is not None:
            solar_plant_generation = sum(model.flow[solar_plant, el_bus, t] for t in model.TIMESTEPS)
            print(solar_plant_generation)
            total_generation += solar_plant_generation

        expr = (fossil_generation - (1-experiment['min_renewable_share'])*total_generation)
        print(expr)
        return expr <= 0

    model.renewable_share_constraint = po.Constraint(rule=renewable_share_rule)

    return model

def renewable_share_test(case_dict, oemof_results, experiment):
    '''
    Testing simulation results for adherance to above defined stability criterion
    '''
    if case_dict['renewable_share_constraint']==True:
        boolean_test = (oemof_results['res_share'] >= experiment['min_renewable_share'])

        if boolean_test == False:
            logging.warning("ATTENTION: Minimal renewable share criterion NOT fullfilled!")
            logging.warning('Number of timesteps not meeting criteria: ' + str(sum(boolean_test)))
            oemof_results.update({'comments': oemof_results['comments'] + 'Renewable share criterion not fullfilled. '})
        else:
            logging.debug("Minimal renewable share is fullfilled.")
    else:
        pass

    return