==========================================
Cost analysis
==========================================
For the costs analysis ultimately governing the optimization and determining the solutions NPV and LCOE, a number of values have to be provided as input parameters (as always, these can be subject to sensitivity analyses). These values are used to calculate the annuity and variable costs applied in oemof-optimizations. The costs' evaluation takes place after the oemof-optimization itself and calculates annuity and variable operation costs of the project.

Input values
-------------
Costs ranging from variable costs per kWh, operational costs per year and investment costs are taken into account in the simulation tool. They are included through a large number of input values.

Financial values are:

* Fuel price (/l) combined with combustion value (kWh/l)
* Price of electricity from national grid
* Taxes (import tax)
* wacc used as discount factor
* Project lifetime

Further parameters are necessary for each cost component:

* Project (-)
* Grid extension (/km)
* Local distribution grid (-)
* PV panels (/kWp)
* Storage (/kWh)
* Fossil-fuelled generator (/kW)

The parameters specifying each of those components are

* Lifetime
* Operation and management costs per year
* Variable costs per kWh
* Investment costs

In this list, the costs of grid extension, local distribution grid and project costs are not specified by variable investment costs. Project investment costs further do not have a specified lifetime and only have to be payed once.

Including costs in oemof optimization
--------------------------------------
**to be updated**

To simplify this large amount of data and enable its integration into the oemof framework, the fixed annuity of each component is calculated.

First the CAPEX of each component has to be calculated. The CAPEX includes its first investment costs as well as re-investments based on it's lifetime and value at project end. For this procedure the following algorithm is used:::

        number_of_investments = int(round(project_life / lifetime))
        # costs with quantity and import tax at t=0
        first_time_investment = investment_t0 * (1+tax)
        for count_of_replacements in range(0, number_of_investments):
            # Very first investment is in year 0

            if count_of_replacements == 0:
                capex = first_time_investment
            else:
                # replacements taking place in year = number_of_replacement * lifetime
                if count_of_replacements * lifetime != project_life:
                    capex = capex + first_time_investment / ((1 + wacc) ** (count_of_replacements * lifetime))
        # Substraction of component value at end of life with last replacement (= number_of_investments - 1)
        if number_of_investments * lifetime > project_life:
            last_investment = first_time_investment / ((1 + wacc) ** ((number_of_investments - 1) * lifetime))
            linear_depreciation_last_investment = last_investment / lifetime
            capex = capex -  linear_depreciation_last_investment * (number_of_investments * lifetime - project_life)

The operation and management costs that have a fix annual value are summarized as OPEX:::

       annuity_factor = 1 / wacc - 1 / (wacc * (1 + wacc) ** project_life)
       OPEX = annual O&M costs * annuity_factor

The present costs are calculated by adding the CAPEX of a component to its OPEX:::

       present cost = CAPEX + OPEX

Factorized with the annuity factor, the annuity is calculated:::

       annuity = present costs / annuity factor

In optimizations, the variable costs from the inputs are equal to the _variable_costs_ of a flow connected to a component. In investment mode, the annuity is equal to the _ep_costs_ (What does this mean).

Case-based cost evaluation
--------------------------------------
Currently, the cost evaluation is performed in a complicated manner and it is necessary to distinguish between cases. This comes from the fact, that in dispatch analyses only the variable costs are optimized, while the optimal energy mix also includes above calculated annuities per component unit. In mixed cases with dispatch (fixed PCC capacities) and optimal energy mix, this issue becomes more complicated.

A simplification that bases the calculation of component costs on its capacities and connected flows should be possible and will be included in the future.
