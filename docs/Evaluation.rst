==========================================
Evaluation of oemof results
==========================================
**to be updated**

The evaluation of the oemof-results is case-specific.

General remarks regarding computation of parameters
---------------------------------------------------
+++++++++++++++++++++
OEM of all components
+++++++++++++++++++++
Objective value of a OEM resulting in a optimal capacity for each component is the imaginary annual value of the timeframe analysed. To allow interpretation as a truly annual value, the objective value has to be corrected by:::

        annuity = obj * 365/evaluated days

When saving the total demand, fuel consumtion or fuel expenditures to the results, the same adjustment has to take place. This allows the computation of the levelized electricity costs (LCOE) of the project:::

        LCOE = annuity / (demand in timeframe * 365/evaluated days) = annuity / total annual demand

And of the net present value NPV:::

        NPV = annuity * annuity factor

To include project development costs, it's annuity and NPV have to be added respectively.

++++++++++++++++++++++++++++++++
Partly OEM and dispatch analysis
++++++++++++++++++++++++++++++++
When including components with fixed capacities in an OEM, ie. by

* adding a fixed-capacity generator with load minimum
* optimizing the capacities of a grid-tied micro grid with fixed point of common coupling

or when performing a dispatch analysis, in which all capacities are fixed, the investment costs of all capacities are not considered. They can not be influenced by the optimization process and thus exempted from calculations. A dispatch analysis thus finds the operation with the least marginal costs. To be able to compare the results later in-between cases, the fixed costs have to be added according to the concept of the analyzed case. This can mean:

* Adding capital costs of the point of common coupling according to it's capacity in case of OEM of an grid-tied micro grid

* Adding capital costs of the point of common coupling according to it's capacity in case of dispatch analysis of an interconnecting micro grid

* Adding capital costs of diesel generators to objective value of OEM with generator with minimal loading
