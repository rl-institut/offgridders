==========================================
General: Adding constraints
==========================================


Sometimes, a scenario analyzed by oemof needs additional constraints for a proper optimization result. As presented in oemof's `readthedocs <https://oemof.readthedocs.io/en/stable/_modules/oemof/solph/constraints.html>`_ this could be as easy as limiting the total investment allowed. In other cases, more elaborate constraints have to be formulated.

In the case of this tool, a constraint defining minimal grid-stabilizing capacities (fossil-fulled generator, storage) was needed. The constraint has to be fullfilled in every time step, which influences the optimization result of the capacities to be installed. The procedure to add this customized constraint shall be described below.


General structure of a constraint
--------------------------------------------

Create a separate file "constraints_custom.py". Load pyomo library and define your constraint. Arguments submitted to the function are the model and  arguments specific to your constraint. Do not forget to describe your constraint for later use.::

        import pyomo.environ as po

        def stability_criterion(model, limit):
            ´´´
            Constraint description
            ´´´
            return model

General code, eg. extracting constant data from the model, will be placed right into the function _stability_criterion_. The rule itself will be placed into the subfunction _stability_rule_, with above mentioned arguments. The using the pyomo function **po.Constraints**, the _stability_rule_ is added to the model and thus the lp file for the optimization.::

        import pyomo.environ as po

        def stability_criterion(model, limit):

            # (1) general code

            def stability_rule(model):

                # (2) value definition

                return # (3) equation expressing constraint

            model.stability_criterion = po.Constraints(rule=stability_rule)

            return model

Defining the constraint
--------------------------------------------

+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Directly accessing attributes of Flows in an oemof-model (1)
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

To directly call values of flows from module, the constraint has to have the oemof-objects of component and bus **directly** as an argument. Then, calling their values is much easier (optional in investment-mode or fixed):::

        # genset capacity subject to oem
        if hasattr(model, "InvestmentFlow"):
                CAP_genset += model.InvestmentFlow.invest[genset, el_bus]
        # genset capacity subject to dispatch
        else:
            CAP_genset = module.flows[genset, el_bus].nominal_capacity

+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Directly accessing timestep values of flows
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

When a bus-component combination is an argument of the constraint, accessing it's connected flow is easy:::

            demand = model.flow[el_bus,sink_demand,t]

When accessing the flows of a storage, one has to make a distinction between a storage subject to investment optimization or dispatch optimization:::

            # Storage subject to OEM
            if hasattr(model, "InvestmentFlow"):
                storage_capacity += model.GenericInvestmentStorageBlock.capacity[storage, t]
            # Fixed storage subject to dispatch
            else:
                storage_capacity += model.GenericStorageBlock.capacity[storage, t]

+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Calling attibutes from the component definitions (2)
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

When a component is an argument of the constraint, accessing it's attributes is easy:::

        invest_relation_output_capacity = storage.invest_relation_output_capacity

Make sure that this value is defined for your component.


+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Equation for pyomo (3)
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

The constraint itself is defined by an equation (<=, ==, >=). Make sure, that your equation does not result in a value (True/False) but in the generation of an commonly applicable rule (?). This can happen if you print out results during coding the constraint and use calls like _model.flow[el_bus,sink_demand,t].value_.::

                expr = CAP_genset + storage_capacity * storage.invest_relation_output_capacity\
                       >= stability_limit * demand

To make sure this rule is applied to every timestep, you can either explicitly loop over the expression - or you perform po.Constraints with the argument model.TIMESTEPS while leaving t as an argument of your rule.::

        model.stability_constraint = po.Constraint(model.TIMESTEPS, rule=stability_rule)

+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Sidenotes: Indirectly accessing attributes of Flows of an oemof-model (1)
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Calling constant attributes of Flows or InvestmentFlows indirectly makes most sense, if a certain class of components/busses is subjected to the constraint and if you can not or do not want to group it's element (?). Possible classes can be:::

* oemof.solph.components.GenericStorage
* oemof.solph.network.Transformer
* oemof.solph.network.Source
* oemof.solph.network.Sink
* oemof.solph.network.Bus

To use a whole class of oemof-objects, it is possible to search for this class in all entries of  module.Flows or module.InvestmentFlow. This way, multiple storages, transformers, ie. can be subject to the constraint without calling them directly.::

        import oemof
        ...
        CAP_genset = 0

        # genset capacity subject to oem (Investment mode)
        if hasattr(model, "InvestmentFlow"):
            for i,o in model.InvestmentFlow:
                if isinstance(i, oemof.solph.network.Transformer)  and str(o)=='bus_electricity_mg':
                    CAP_genset += model.InvestmentFlow.invest[i,o]


        # genset capacity subject to dispatch
        else:
            for i,o in model.Flows:
                if isinstance(i, oemof.solph.network.Transformer)  and str(o)=='bus_electricity_mg':
                    CAP_genset += module.flows[i, o].nominal_capacity

This is not used in the tool, as calling for the general transformer would also include the PCC of an interconnected micro grid without taking into account grid availability - the stability constraint would always be full-filled, even though the grid could not aid the MG during blackouts.

It is not possible to call an element (given flow) by the name of the component "component_name" and bus "busname". If names are to be used, then it is necessary to loop over all InvestmentFlow entries and check manually for those names. With multiple instances like this, it might be better to access the oemof-object directly (see above section).

The code to access a specific transformer with the name 'transformer_fuel_generator',  which can either be subject to an Investment optimization or a dispatch optimization, is:::

        CAP_genset = 0

        # genset capacity subject to oem (Investment mode)
        if hasattr(model, "InvestmentFlow"):
            for i,o in model.InvestmentFlow.invest:
                if str(i)=='transformer_fuel_generator' and str(o)=='bus_electricity_mg':
                    if isinstance(model.InvestmentFlow.invest[i, o].value, int):
                        CAP_genset +=model.InvestmentFlow.invest[i, o].value

        # genset capacity subject to dispatch
        else:
            for i,o in model.Flows:
                if str(i)=='transformer_fuel_generator' and str(o)=='bus_electricity_mg':
                    CAP_genset += module.flows[i, o].nominal_capacity

Final constraint:
--------------------

All blocks (1), (2) and (3) are included:::

        def stability_criterion(model, stability_limit, storage, sink_demand, genset, el_bus):
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


To verify the simulation and make sure, that the rule is properly included, the optimization results are later on tested:::

        boolean_test = [
            genset_capacity + storage_capacity[t] * experiment['storage_Crate'] \
            >= experiment['stability_limit'] * demand_profile[t]
            for t in demand_profile.index]

        if any(boolean_test) == False:
            logging.info("ATTENTION: Stability criterion NOT fullfilled!")
        else:
            logging.info("Stability criterion is fullfilled.")

+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Including the constraint into the oemof-model
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++



A constraint can be added to the oemof energysystem after adding all components and creating the model using solph:::

         import constraints_custom as constraints
         ...
         micro_grid_system = solph.EnergySystem(timeindex=date_time_index)
         ... # Lenghly model description)
         model = solph.Model(micro_grid_system)

         limit=0.5
         constraints.stability_criterion(model, limit)

         model.solve(solver = solver)

