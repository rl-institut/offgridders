==========================================
Sensitivity analysis
==========================================
**to be updated**

The sensitivity analysis is based on parameters (input values) that can be set as constants or as intervals:::

        sensitivity_constants = {'variable_name':  constant value}

        sensitivity_bounds = {'variable_name':
            {'min': min_value,  'max': max_value,     'step': steplenght}}

If a parameter is defined twice - in sensitivity_constants as well as in sensitivity_bounds -, a warning will be displayed. The proceeding simulations will use the constant value of the parameter.