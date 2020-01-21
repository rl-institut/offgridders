def present_value_of_changing_fuel_price(
    fuel_price, project_lifetime, wacc, crf, fuel_price_change_annual
):
    cash_flow_fuel_l = 0
    fuel_price_i = fuel_price
    for i in range(0, project_lifetime + 1):
        print(i, fuel_price_i)
        cash_flow_fuel_l += fuel_price_i / (1 + wacc) ** (i)
        fuel_price_i = fuel_price_i * (1 + fuel_price_change_annual)
    present_value_changing_fuel_price = cash_flow_fuel_l * crf
    return present_value_changing_fuel_price


def crf(project_life, wacc):
    crf = (wacc * (1 + wacc) ** project_life) / ((1 + wacc) ** project_life - 1)
    print(crf)
    return crf


fuel_price = present_value_of_changing_fuel_price(0.6, 20, 0.16, crf(20, 0.16), 0.0)
print(fuel_price)
