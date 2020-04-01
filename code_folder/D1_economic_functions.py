class economics:
    # annuity factor to calculate present value of cash flows
    def annuity_factor(project_life, wacc):
        # discount_rate was replaced here by wacc
        annuity_factor = 1 / wacc - 1 / (wacc * (1 + wacc) ** project_life)
        return annuity_factor

    # accounting factor to translate present value to annual cash flows
    def crf(project_life, wacc):
        crf = (wacc * (1 + wacc) ** project_life) / ((1 + wacc) ** project_life - 1)
        return crf

    def present_value_of_changing_fuel_price(
        fuel_price, project_lifetime, wacc, crf, fuel_price_change_annual
    ):
        cash_flow_fuel_l = 0
        fuel_price_i = fuel_price
        for i in range(0, project_lifetime):
            cash_flow_fuel_l += fuel_price_i / (1 + wacc) ** (i)
            fuel_price_i = fuel_price_i * (1 + fuel_price_change_annual)
        present_value_changing_fuel_price = cash_flow_fuel_l * crf
        return present_value_changing_fuel_price

    def capex_from_investment(investment_t0, lifetime, project_life, wacc, tax):
        # [quantity, investment, installation, weight, lifetime, om, first_investment]
        if project_life == lifetime:
            number_of_investments = 1
        else:
            number_of_investments = int(round(project_life / lifetime + 0.5))
        # costs with quantity and import tax at t=0
        first_time_investment = investment_t0 * (1 + tax)

        for count_of_replacements in range(0, number_of_investments):
            # Very first investment is in year 0
            if count_of_replacements == 0:
                capex = first_time_investment
            else:
                # replacements taking place in year = number_of_replacement * lifetime
                if count_of_replacements * lifetime != project_life:
                    capex = capex + first_time_investment / (
                        (1 + wacc) ** (count_of_replacements * lifetime)
                    )

        # Substraction of component value at end of life with last replacement (= number_of_investments - 1)
        if number_of_investments * lifetime > project_life:
            last_investment = first_time_investment / (
                (1 + wacc) ** ((number_of_investments - 1) * lifetime)
            )
            linear_depreciation_last_investment = last_investment / lifetime
            capex = capex - linear_depreciation_last_investment * (
                number_of_investments * lifetime - project_life
            )

        return capex

    def annuity(present_value, crf):
        annuity = present_value * crf
        return annuity

    def present_value_from_annuity(annuity, annuity_factor):
        present_value = annuity * annuity_factor
        return present_value
