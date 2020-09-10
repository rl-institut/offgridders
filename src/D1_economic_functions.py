import logging


def annuity_factor(project_life, wacc):
    """
    Annuity factor to calculate present value of cash flows (?)

    Parameters
    ----------
    project_life: int
        Years of projected lifetime

    wacc: float
        Discounting Factor

    Returns
    -------
    Annuity_factor: float

    """
    # discount_rate was replaced here by wacc
    annuity_factor = 1 / wacc - 1 / (wacc * (1 + wacc) ** project_life)
    return annuity_factor



def crf(project_life, wacc):
    """
    Accounting factor to translate present value to annual cash flows

    Parameters
    ----------
    project_life: int
        Years of projects lifetime (?)

    wacc: float
        Discounting Factor

    Returns
    -------
    crf: float

    """
    crf = (wacc * (1 + wacc) ** project_life) / ((1 + wacc) ** project_life - 1)
    return crf


def present_value_of_changing_fuel_price(
    fuel_price, project_lifetime, wacc, crf, fuel_price_change_annual
):
    """

    Parameters
    ----------
    fuel_price:float
        Fuel price per liter

    project_lifetime: int
        Number of projects lifetime years

    wacc: float
        Discount factor

    crf: float

    fuel_price_change_annual: float
        Change in annual price

    Returns
    -------
    present_value_changing_fuel_price: float
        Change of fuel price in the future

    """
    if fuel_price_change_annual != 0:
        logging.error(
            "You chose parameter 'fuel_price_change_annual' unequal zero. "
            "This calculation is still faulty and you should check the resulting fuel price. "
            "It would be better if you set your fuel price by hand."
        )

        cash_flow_fuel_l = 0
        fuel_price_i = fuel_price
        for i in range(0, project_lifetime):
            cash_flow_fuel_l += fuel_price_i / (1 + wacc) ** (i)
            fuel_price_i = fuel_price_i * (1 + fuel_price_change_annual)
        present_value_changing_fuel_price = cash_flow_fuel_l * crf
        logging.info(
            " The resulting fuel price is: " + str(present_value_changing_fuel_price)
        )
    else:
        present_value_changing_fuel_price = fuel_price
        logging.info(
            "Simulation will run with a fuel price of "
            + str(present_value_changing_fuel_price)
        )
    return present_value_changing_fuel_price


def capex_from_investment(investment_t0, lifetime, project_life, wacc, tax):
    """

    Parameters
    ----------
    investment_t0: float

    lifetime:int

    project_life:int

    wacc: float
        Discount factor

    tax:int
        Import tax?

    Returns
    -------

    """
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
        ) / ((1 + wacc) ** (project_life))

    return capex


def annuity(present_value, crf):
    """
    Calculates the regular payment including interests(?)

    Parameters
    ----------
    present_value: float
        Current price

    crf:float


    Returns
    -------
    Annuity: float

    """
    annuity = present_value * crf
    return annuity


def present_value_from_annuity(annuity, annuity_factor):
    """
    Calculates the present value of the proyect from the calculated annuity and its factor

    Parameters
    ----------
    annuity: float
        Sequential payments

    annuity_factor: float
        ?

    Returns
    -------

    """
    present_value = annuity * annuity_factor
    return present_value
