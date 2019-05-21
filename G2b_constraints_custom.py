'''
For defining custom constraints of the micro grid solutions
'''
import pyomo.environ as po
import logging
import pandas as pd

class stability_criterion():

    def backup(model, case_dict, experiment, storage, sink_demand, genset, pcc_consumption, source_shortage, el_bus_ac, el_bus_dc):
        stability_limit = experiment['stability_limit']
        ## ------- Get CAP genset ------- #
        CAP_genset = 0
        if case_dict['genset_fixed_capacity'] != None:
            if case_dict['genset_fixed_capacity']==False:
                for number in range(1, case_dict['number_of_equal_generators']+ 1):
                    CAP_genset += model.InvestmentFlow.invest[genset[number], el_bus_ac]
            elif isinstance(case_dict['genset_fixed_capacity'], float):
                for number in range(1, case_dict['number_of_equal_generators'] + 1):
                    CAP_genset += model.flows[genset[number], el_bus_ac].nominal_value

        ## ------- Get CAP PCC ------- #
        CAP_pcc = 0
        if case_dict['pcc_consumption_fixed_capacity'] != None:
            if case_dict['pcc_consumption_fixed_capacity'] == False:
                CAP_pcc += model.InvestmentFlow.invest[pcc_consumption, el_bus_ac]
            elif isinstance(case_dict['pcc_consumption_fixed_capacity'], float):
                CAP_pcc += case_dict['pcc_consumption_fixed_capacity'] # this didnt work - model.flows[pcc_consumption, el_bus_ac].nominal_value

        def stability_rule_capacity(model, t):
            expr = CAP_genset
            ## ------- Get demand at t ------- #
            demand = model.flows[el_bus_ac, sink_demand].actual_value[t] * model.flows[el_bus_ac, sink_demand].nominal_value
            expr += - stability_limit * demand
            ## ------- Get shortage at t------- #
            if case_dict['allow_shortage'] == True:
                shortage = model.flow[source_shortage,el_bus_ac,t]
                #todo is this correct?
                expr += + stability_limit * shortage
            ##---------Grid consumption t-------#
            # this should not be actual consumption but possible one  - like grid_availability[t]*pcc_consumption_cap
            if case_dict['pcc_consumption_fixed_capacity'] != None:
                expr += CAP_pcc * experiment['grid_availability'][t]

            ## ------- Get stored capacity storage at t------- #
            if case_dict['storage_fixed_capacity'] != None:
                stored_electricity = 0
                if case_dict['storage_fixed_capacity'] == False:  # Storage subject to OEM
                    stored_electricity += model.GenericInvestmentStorageBlock.capacity[storage, t]  - experiment['storage_capacity_min'] * model.GenericInvestmentStorageBlock.invest[storage]
                elif isinstance(case_dict['storage_fixed_capacity'], float): # Fixed storage subject to dispatch
                    stored_electricity += model.GenericStorageBlock.capacity[storage, t] - experiment['storage_capacity_min'] * storage.nominal_capacity
                else:
                    logging.warning("Error: 'storage_fixed_capacity' can only be None, False or float.")
                expr += stored_electricity * experiment['storage_Crate_discharge'] \
                        * experiment['storage_efficiency_discharge'] \
                        * experiment['inverter_dc_ac_efficiency']
            return (expr >= 0)

        def stability_rule_power(model, t):
            expr = CAP_genset
            ## ------- Get demand at t ------- #
            demand = model.flows[el_bus_ac, sink_demand].actual_value[t] * model.flows[el_bus_ac, sink_demand].nominal_value
            expr += - stability_limit * demand
            ## ------- Get shortage at t------- #
            if case_dict['allow_shortage'] == True:
                shortage = model.flow[source_shortage,el_bus_ac,t]
                #todo is this correct?
                expr += + stability_limit * shortage
            ##---------Grid consumption t-------#
            # this should not be actual consumption but possible one  - like grid_availability[t]*pcc_consumption_cap
            if case_dict['pcc_consumption_fixed_capacity'] != None:
                expr += CAP_pcc * experiment['grid_availability'][t]

            ## ------- Get power of storage ------- #
            if case_dict['storage_fixed_power'] != None:
                storage_power = 0
                if case_dict['storage_fixed_capacity'] == False:
                    storage_power += model.InvestmentFlow.invest[storage, el_bus_dc]
                elif isinstance(case_dict['storage_fixed_capacity'], float):
                    storage_power += case_dict['storage_fixed_power']
                else:
                    logging.warning("Error: 'storage_fixed_power' can only be None, False or float.")

                expr += storage_power * experiment['inverter_dc_ac_efficiency']
            return (expr >= 0)

        model.stability_constraint = po.Constraint(model.TIMESTEPS, rule=stability_rule_capacity)
        model.stability_constraint_power = po.Constraint(model.TIMESTEPS, rule=stability_rule_power)
        return model

    def backup_test(case_dict, oemof_results, experiment, e_flows_df):
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

            boolean_test = [
                genset_capacity
                + (stored_electricity[t] - oemof_results['capacity_storage_kWh'] *  experiment['storage_capacity_min'])
                *  experiment['storage_Crate_discharge'] * experiment['storage_efficiency_discharge'] * experiment['inverter_dc_ac_efficiency']
                + pcc_capacity[t]
                >= experiment['stability_limit'] * (demand_profile[t] - shortage[t])
                for t in range(0, len(demand_profile.index))
                ]

            if all(boolean_test) == True:
                logging.debug("Stability criterion is fullfilled.")
            else:
                ratio = pd.Series([
                    (genset_capacity
                     + (stored_electricity[t] - oemof_results['capacity_storage_kWh'] * experiment['storage_capacity_min'])
                     * experiment['storage_Crate_discharge'] * experiment['storage_efficiency_discharge'] * experiment['inverter_dc_ac_efficiency']
                     + pcc_capacity[t]
                     - experiment['stability_limit'] * (demand_profile[t] - shortage[t]))
                    / (experiment['peak_demand'])
                    for t in range(0, len(demand_profile.index))], index=demand_profile.index)
                ratio_below_zero=ratio.clip_upper(0)
                stability_criterion.test_warning(ratio_below_zero, oemof_results, boolean_test)
        else:
            pass

    def hybrid(model, case_dict, experiment, storage, sink_demand, genset, pcc_consumption, source_shortage,
               el_bus_ac, el_bus_dc):

        stability_limit = experiment['stability_limit']

        def stability_rule_capacity(model, t):
            expr = 0
            ## ------- Get demand at t ------- #
            demand = model.flows[el_bus_ac, sink_demand].actual_value[t] * model.flows[el_bus_ac, sink_demand].nominal_value
            expr += - stability_limit * demand

            ## ------- Get shortage at t------- #
            if case_dict['allow_shortage'] == True:
                shortage = model.flow[source_shortage, el_bus_ac, t]
                expr += + stability_limit * shortage

            ## ------- Generation Diesel ------- #
            if case_dict['genset_fixed_capacity'] != None:
                for number in range(1, case_dict['number_of_equal_generators'] + 1):
                    expr += model.flow[genset[number], el_bus_ac, t]

            ##---------Grid consumption t-------#
            if case_dict['pcc_consumption_fixed_capacity'] != None:
               expr += model.flow[pcc_consumption, el_bus_ac, t]

            ## ------- Get stored capacity storage at t------- #
            if case_dict['storage_fixed_capacity'] != None:
                stored_electricity = 0
                if case_dict['storage_fixed_capacity'] == False:  # Storage subject to OEM
                    stored_electricity += model.GenericInvestmentStorageBlock.capacity[storage, t]  - experiment['storage_soc_min'] * model.GenericInvestmentStorageBlock.invest[storage]
                elif isinstance(case_dict['storage_fixed_capacity'], float): # Fixed storage subject to dispatch
                    stored_electricity += model.GenericStorageBlock.capacity[storage, t] - experiment['storage_soc_min'] * storage.nominal_capacity
                else:
                    logging.warning("Error: 'storage_fixed_capacity' can only be None, False or float.")
                expr += stored_electricity * experiment['storage_Crate_discharge'] \
                        * experiment['storage_efficiency_discharge'] \
                        * experiment['inverter_dc_ac_efficiency']
            return (expr >= 0)

        def stability_rule_power(model, t):
            expr = 0
            ## ------- Get demand at t ------- #
            demand = model.flows[el_bus_ac, sink_demand].actual_value[t] * model.flows[el_bus_ac, sink_demand].nominal_value
            expr += - stability_limit * demand

            ## ------- Get shortage at t------- #
            if case_dict['allow_shortage'] == True:
                shortage = model.flow[source_shortage, el_bus_ac, t]
                expr += + stability_limit * shortage

            ## ------- Generation Diesel ------- #
            if case_dict['genset_fixed_capacity'] != None:
                for number in range(1, case_dict['number_of_equal_generators'] + 1):
                    expr += model.flow[genset[number], el_bus_ac, t]

            ##---------Grid consumption t-------#
            if case_dict['pcc_consumption_fixed_capacity'] != None:
               expr += model.flow[pcc_consumption, el_bus_ac, t]

            ## ------- Get power of storage ------- #
            if case_dict['storage_fixed_power'] != None:
                storage_power = 0
                if case_dict['storage_fixed_capacity'] == False:
                    storage_power += model.InvestmentFlow.invest[storage, el_bus_dc]
                elif isinstance(case_dict['storage_fixed_capacity'], float):
                    storage_power += case_dict['storage_fixed_power']
                else:
                    logging.warning("Error: 'storage_fixed_power' can only be None, False or float.")

                expr += storage_power * experiment['inverter_dc_ac_efficiency']
            return (expr >= 0)

        model.stability_constraint_capacity = po.Constraint(model.TIMESTEPS, rule=stability_rule_capacity)
        model.stability_constraint_power = po.Constraint(model.TIMESTEPS, rule=stability_rule_power)
        return model

    def hybrid_test(case_dict, oemof_results, experiment, e_flows_df):
        '''
            Testing simulation results for adherance to above defined stability criterion
            #todo actually this does not test the stability_share_power criterion, which includes the storage power!
        '''
        if case_dict['stability_constraint'] != False:
            demand_profile = e_flows_df['Demand']

            if case_dict['allow_shortage'] == True:
                shortage = e_flows_df['Demand shortage']
            else:
                shortage = pd.Series([0 for t in demand_profile.index], index=demand_profile.index)

            if ('Stored capacity' in e_flows_df.columns):
                stored_electricity = e_flows_df['Stored capacity']
            else:
                stored_electricity = pd.Series([0 for t in demand_profile.index], index=demand_profile.index)

            if ('Consumption from main grid (MG side)' in e_flows_df.columns):
                pcc_feedin = e_flows_df['Consumption from main grid (MG side)']
            else:
                pcc_feedin = pd.Series([0 for t in demand_profile.index], index=demand_profile.index)

            if ('Genset generation' in e_flows_df.columns):
                genset_generation = e_flows_df['Genset generation']
            else:
                genset_generation = pd.Series([0 for t in demand_profile.index], index=demand_profile.index)

            boolean_test = [
                genset_generation[t]
                + (stored_electricity[t] - oemof_results['capacity_storage_kWh'] * experiment['storage_soc_min'])
                     * experiment['storage_Crate_discharge'] * experiment['storage_efficiency_discharge'] * experiment['inverter_dc_ac_efficiency']
                + pcc_feedin[t]
                >= experiment['stability_limit'] * (demand_profile[t] - shortage[t])
                for t in range(0, len(demand_profile.index))
            ]

            if all(boolean_test) == True:
                logging.debug("Stability criterion is fullfilled.")
            else:
                ratio = pd.Series([
                    (genset_generation[t]
                     + (stored_electricity[t] - oemof_results['capacity_storage_kWh'] * experiment['storage_soc_min'])
                     * experiment['storage_Crate_discharge'] * experiment['storage_efficiency_discharge'] * experiment['inverter_dc_ac_efficiency']
                     + pcc_feedin[t] - experiment['stability_limit'] * (
                                 demand_profile[t] - shortage[t]))
                    / (experiment['peak_demand_ac'])
                    for t in range(0, len(demand_profile.index))], index=demand_profile.index)
                ratio_below_zero = ratio.clip_upper(0)
                stability_criterion.test_warning(ratio_below_zero, oemof_results, boolean_test)

        else:
            pass

        return

    def usage(model, case_dict, experiment, storage, sink_demand, genset, pcc_consumption, source_shortage,
               el_bus):

        stability_limit = experiment['stability_limit']

        def stability_rule(model, t):
            expr = 0
            ## ------- Get demand at t ------- #
            demand = model.flows[el_bus, sink_demand].actual_value[t] * model.flows[el_bus, sink_demand].nominal_value

            expr += - stability_limit * demand

            ## ------- Get shortage at t------- #
            if case_dict['allow_shortage'] == True:
                shortage = model.flow[source_shortage, el_bus, t]
                expr += stability_limit * shortage

            ## ------- Generation Diesel ------- #
            if case_dict['genset_fixed_capacity'] != None:
                for number in range(1, case_dict['number_of_equal_generators'] + 1):
                    expr += model.flow[genset[number], el_bus, t]

            ##---------Grid consumption t-------#
            if case_dict['pcc_consumption_fixed_capacity'] != None:
               expr += model.flow[pcc_consumption, el_bus, t]

            ## ------- Get discharge storage at t------- #
            if case_dict['storage_fixed_capacity'] != None:
                expr += model.flow[storage, el_bus, t] * experiment['inverter_dc_ac_efficiency']
            return (expr >= 0)

        model.stability_constraint = po.Constraint(model.TIMESTEPS, rule=stability_rule)

        return model

    def usage_test(case_dict, oemof_results, experiment, e_flows_df):
        '''
            Testing simulation results for adherance to above defined stability criterion
        '''
        if case_dict['stability_constraint'] != False:
            demand_profile = e_flows_df['Demand']

            if case_dict['allow_shortage'] == True:
                shortage = e_flows_df['Demand shortage']
            else:
                shortage = pd.Series([0 for t in demand_profile.index], index=demand_profile.index)

            if ('Storage discharge' in e_flows_df.columns):
                storage_discharge = e_flows_df['Storage discharge']
            else:
                storage_discharge = pd.Series([0 for t in demand_profile.index], index=demand_profile.index)

            if ('Consumption from main grid (MG side)' in e_flows_df.columns):
                pcc_feedin = e_flows_df['Consumption from main grid (MG side)']
            else:
                pcc_feedin = pd.Series([0 for t in demand_profile.index], index=demand_profile.index)

            if ('Genset generation' in e_flows_df.columns):
                genset_generation = e_flows_df['Genset generation']
            else:
                genset_generation = pd.Series([0 for t in demand_profile.index], index=demand_profile.index)

            boolean_test = [
                genset_generation[t] + storage_discharge[t] * experiment['inverter_dc_ac_efficiency'] + pcc_feedin[t] \
                >= experiment['stability_limit'] * (demand_profile[t] - shortage[t])
                for t in range(0, len(demand_profile.index))
            ]

            if all(boolean_test) == True:
                logging.debug("Stability criterion is fullfilled.")
            else:
                ratio = pd.Series([
                    (genset_generation[t] + storage_discharge[t] * experiment['inverter_dc_ac_efficiency'] + pcc_feedin[t] - experiment['stability_limit'] * (
                                 demand_profile[t] - shortage[t]))
                    / (experiment['peak_demand'])
                    for t in range(0, len(demand_profile.index))], index=demand_profile.index)
                ratio_below_zero = ratio.clip_upper(0)
                stability_criterion.test_warning(ratio_below_zero, oemof_results, boolean_test)
        else:
            pass

        return

    def test_warning(ratio_below_zero, oemof_results, boolean_test):
        if abs(ratio_below_zero.values.min()) < 10 ** (-6):
            logging.warning(
                "Stability criterion is strictly not fullfilled, but deviation is less then e6.")
        else:
            logging.warning("ATTENTION: Stability criterion NOT fullfilled!")
            logging.warning('Number of timesteps not meeting criteria: ' + str(sum(boolean_test)))
            logging.warning('Deviation from stability criterion: ' + str(
                ratio_below_zero.values.mean()) + '(mean) / ' + str(
                ratio_below_zero.values.min()) + '(max).')
            oemof_results.update({'comments': oemof_results[
                                                  'comments'] + 'Stability criterion not fullfilled (max deviation ' + str(
                round(100 * ratio_below_zero.values.min(), 4)) + '%). '})
        return

class renewable_criterion():
    def share(model, case_dict, experiment, genset, pcc_consumption, solar_plant, wind_plant, el_bus_ac, el_bus_dc): #wind_plant
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
                for number in range(1, case_dict['number_of_equal_generators'] + 1):
                    genset_generation_kWh = sum(model.flow[genset[number], el_bus_ac, :])
                    total_generation += genset_generation_kWh
                    fossil_generation += genset_generation_kWh

            if pcc_consumption is not None:
                pcc_consumption_kWh = sum(model.flow[pcc_consumption, el_bus_ac, :])
                total_generation += pcc_consumption_kWh
                fossil_generation += pcc_consumption_kWh * (1 - experiment['maingrid_renewable_share'])

            if solar_plant is not None:
                solar_plant_generation = sum(model.flow[solar_plant, el_bus_dc, :])
                total_generation += solar_plant_generation

            if wind_plant is not None:
                wind_plant_generation = sum(model.flow[wind_plant, el_bus_ac, :])
                total_generation += wind_plant_generation

            expr = (fossil_generation - (1-experiment['min_renewable_share'])*total_generation)
            return expr <= 0

        model.renewable_share_constraint = po.Constraint(rule=renewable_share_rule)

        return model

    def share_test(case_dict, oemof_results, experiment):
        '''
        Testing simulation results for adherance to above defined stability criterion
        '''
        if case_dict['renewable_share_constraint']==True:
            boolean_test = (oemof_results['res_share'] >= experiment['min_renewable_share'])
            if boolean_test == False:
                deviation = (experiment['min_renewable_share'] - oemof_results['res_share']) /experiment['min_renewable_share']
                if abs(deviation) < 10 ** (-6):
                    logging.warning(
                        "Minimal renewable share criterion strictly not fullfilled, but deviation is less then e6.")
                else:
                    logging.warning("ATTENTION: Minimal renewable share criterion NOT fullfilled!")
                    oemof_results.update({'comments': oemof_results['comments'] + 'Renewable share criterion not fullfilled. '})
            else:
                logging.debug("Minimal renewable share is fullfilled.")
        else:
            pass

        return

class battery_management():
    def forced_charge(model, case_dict, el_bus_dc, storage, experiment):
        ## ------- Get CAP Storage ------- #
        CAP_storage = 0
        if case_dict['storage_fixed_capacity'] != None:
            if case_dict['storage_fixed_capacity'] == False:
                CAP_storage += model.GenericInvestmentStorageBlock.invest[storage]
            elif isinstance(case_dict['storage_fixed_capacity'], float):
                CAP_storage += storage.nominal_capacity

        m = - experiment['storage_Crate_charge']/ (experiment['storage_soc_max']-experiment['storage_soc_min'])

        n = experiment['storage_Crate_charge'] * CAP_storage \
            * (1 + experiment['storage_soc_min']/(experiment['storage_soc_max']-experiment['storage_soc_min']))

        def linear_charge(model, t):
            ## ------- Get storaged electricity at t------- #
            stored_electricity = 0
            expr = 0
            if case_dict['storage_fixed_capacity'] != None:
                if case_dict['storage_fixed_capacity'] == False:  # Storage subject to OEM
                    stored_electricity += model.GenericInvestmentStorageBlock.capacity[storage, t]
                elif isinstance(case_dict['storage_fixed_capacity'], float):  # Fixed storage subject to dispatch
                    stored_electricity += model.GenericStorageBlock.capacity[storage, t]

                # Linearization
                expr = m * stored_electricity + n #* 0.99

                # Only apply linearization if no blackout occurs
                expr = expr * experiment['grid_availability'][t]

                # Actual charge
                expr += - model.flow[el_bus_dc, storage, t]
            return (expr <= 0)

        model.forced_charge_linear = po.Constraint(model.TIMESTEPS, rule=linear_charge)

        return model

    def forced_charge_test(case_dict, oemof_results, experiment, e_flows_df):
        '''
        Testing simulation results for adherance to above defined criterion
        '''
        if case_dict['force_charge_from_maingrid']==True:
            boolean_test = [(experiment['storage_Crate_charge'] * oemof_results['capacity_storage_kWh'] \
                          * (1+experiment['storage_soc_min']/(experiment['storage_soc_max']-experiment['storage_soc_min']))
                             + (oemof_results['capacity_storage_kWh'] - e_flows_df['Stored capacity'][t])
                             / (experiment['storage_soc_max']-experiment['storage_soc_min']))
                            *e_flows_df['Grid availability'][t]
                            <= e_flows_df['Storage charge DC'][t] for t in range(0, len(e_flows_df.index))]

            if all(boolean_test) == True:
                logging.debug("Battery is always charged when grid availabile (linearized).")
            else:

                deviation = pd.Series([(experiment['storage_Crate_charge'] * oemof_results['capacity_storage_kWh'] \
                          * (1+experiment['storage_soc_min']/(experiment['storage_soc_max']-experiment['storage_soc_min']))
                             + (oemof_results['capacity_storage_kWh'] - e_flows_df['Stored capacity'][t])
                             / (experiment['storage_soc_max']-experiment['storage_soc_min']))*e_flows_df['Grid availability'][t]
                                       - e_flows_df['Storage charge DC'][t] for t in range(0, len(e_flows_df.index))], index=e_flows_df.index)

                if max(deviation) < 10 ** (-6):
                    logging.warning(
                        "Battery charge when grid available not as high as need be, but deviation is less then e6.")
                else:
                    logging.warning("ATTENTION: Battery charge at grid availability does not take place adequately!")
                    oemof_results.update({'comments': oemof_results['comments'] + 'Forced battery charge criterion not fullfilled. '})

        return

    def discharge_only_at_blackout(model, case_dict, el_bus, storage, experiment):
        grid_inavailability = 1-experiment['grid_availability']

        def discharge_rule_upper(model, t):
            expr = 0
            stored_electricity = 0

            if case_dict['storage_fixed_capacity'] != None:
                # Battery discharge flow
                expr += model.flow[storage, el_bus, t]
                # Get stored electricity at t
                if case_dict['storage_fixed_capacity'] == False:  # Storage subject to OEM
                    stored_electricity += model.GenericInvestmentStorageBlock.capacity[storage, t]
                elif isinstance(case_dict['storage_fixed_capacity'], float):  # Fixed storage subject to dispatch
                    stored_electricity += model.GenericStorageBlock.capacity[storage, t]

                # force discharge to zero when grid available
                expr += - stored_electricity * grid_inavailability[t]


            return (expr <= 0)

        model.discharge_only_at_blackout_constraint = po.Constraint(model.TIMESTEPS, rule=discharge_rule_upper)

        return model

    def discharge_only_at_blackout_test(case_dict, oemof_results, e_flows_df):
        '''
        Testing simulation results for adherance to above defined criterion
        '''
        if case_dict['discharge_only_when_blackout']==True and case_dict['storage_fixed_capacity'] != None:
            boolean_test = [e_flows_df['Storage discharge DC'][t]
                             <= (1-e_flows_df['Grid availability'][t]) * e_flows_df['Stored capacity'][t]
                             for t in range(0, len(e_flows_df.index))]

            if all(boolean_test) == True:
                logging.debug("Battery only discharged when grid unavailable.")
            else:
                ratio = pd.Series([(e_flows_df['Storage discharge DC'][t] - (1-e_flows_df['Grid availability'][t]) * e_flows_df['Stored capacity'][t])
                                   for t in range(0, len(e_flows_df.index))], index=e_flows_df.index)

                if max(ratio) < 10 ** (-6):
                    logging.warning(
                        "Battery discharge when grid available, but deviation is less then e6.")
                else:
                    logging.warning("ATTENTION: Battery charge when grid available!")
                    oemof_results.update({'comments': oemof_results['comments'] + 'Limitation of battery discharge to blackout not fullfilled. '})

        return

class ac_dc_bus:

    def inverter_only_at_blackout(model, case_dict, el_bus, inverter, experiment):
        grid_inavailability = 1-experiment['grid_availability']

        ## ------- Get CAP inverter ------- #
        CAP_inverter = 0
        if case_dict['inverter_dc_ac_fixed_capacity'] != None:
            if case_dict['inverter_dc_ac_fixed_capacity']==False:
                CAP_inverter += model.InvestmentFlow.invest[el_bus, inverter]
            elif isinstance(case_dict['inverter_dc_ac_fixed_capacity'], float):
                CAP_inverter += model.flows[el_bus, inverter].nominal_value

        def inverter_rule_upper(model, t):
            # Inverter flow
            expr = 0
            if case_dict['inverter_dc_ac_fixed_capacity'] != None:
                expr += model.flow[el_bus, inverter, t]
            # force discharge to zero when grid available
            expr += - CAP_inverter * grid_inavailability[t]
            return (expr <= 0)

        model.inverter_only_at_blackout = po.Constraint(model.TIMESTEPS, rule=inverter_rule_upper)

        return model

    def inverter_only_at_blackout_test(case_dict, oemof_results, e_flows_df):
        '''
        Testing simulation results for adherance to above defined criterion
        '''

        if case_dict['enable_inverter_only_at_backout']==True and case_dict['inverter_dc_ac_fixed_capacity'] != None:
            boolean_test = [e_flows_df['Inverter input'][t]
                             <= (1-e_flows_df['Grid availability'][t]) * oemof_results['capacity_inverter_dc_ac_kW']
                             for t in range(0, len(e_flows_df.index))]

            if all(boolean_test) == True:
                logging.debug("Battery only discharged when grid unavailable.")
            else:
                ratio = pd.Series([(e_flows_df['Inverter input'][t] - (1-e_flows_df['Grid availability'][t]) * oemof_results['capacity_inverter_dc_ac_kW'])
                                   for t in range(0, len(e_flows_df.index))], index=e_flows_df.index)

                if max(ratio) < 10 ** (-6):
                    logging.warning(
                        "Inverter use when grid available, but deviation is less then e6.")
                else:
                    logging.warning("ATTENTION: Inverter use when grid available!")
                    oemof_results.update({'comments': oemof_results['comments'] + 'Inverter use when grid available. '})

        return

class shortage_constraints:

    # todo shortage constraint / stbaility constraint only relates to AC bus
    def timestep(model, case_dict, experiment, el_bus, sink_demand, source_shortage):

        def stability_per_timestep_rule(model, t):
            expr = 0
            ## ------- Get demand at t ------- #
            demand = model.flows[el_bus, sink_demand].actual_value[t] * model.flows[el_bus, sink_demand].nominal_value
            expr += experiment['shortage_max_timestep'] * demand
            ## ------- Get shortage at t------- #
            if case_dict['allow_shortage'] == True:
                expr += - model.flow[source_shortage,el_bus,t]

            return (expr >= 0)

        model.stability_constraint = po.Constraint(model.TIMESTEPS, rule=stability_per_timestep_rule)

        return model
