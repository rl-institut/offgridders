from pytest import approx
import src.D1_economic_functions as D1
import logging


def test_crf():
    project_lifetime = 10
    wacc = 0.1
    crf = D1.crf(project_lifetime, wacc)
    exp = 0.163
    assert exp == approx(
        crf, rel=0.01
    ), f"With a project lifetime of {project_lifetime} and a WACC of {wacc}, the CRF was expected to be {exp}, but it is {crf}."


def test_present_value_of_changing_fuel_price_with_fuel_price_change_annual_0(caplog):
    fuel_price = 1
    project_lifetime = 2
    wacc = 0.05
    crf = D1.crf(project_lifetime, wacc)
    fuel_price_change_annual = 0.0
    with caplog.at_level(logging.INFO):
        present_value_of_changing_fuel_price = D1.present_value_of_changing_fuel_price(
            fuel_price, project_lifetime, wacc, crf, fuel_price_change_annual
        )
    assert (
        "Simulation will run with a fuel price of" in caplog.text
    ), f"An logging.info message should have been logged, as otherwise this indicates that the wrong part of the if-statement is entered"
    assert (
        fuel_price == present_value_of_changing_fuel_price
    ), f"The fuel price should be identical to the present value of the fuel price when there is no annual fuel price change but this is not the case ({fuel_price}/{present_value_of_changing_fuel_price})"


def test_present_value_of_changing_fuel_price_with_fuel_price_change_annual_not_0(
    caplog,
):
    fuel_price = 1
    project_lifetime = 2
    wacc = 0.05
    crf = D1.crf(project_lifetime, wacc)
    fuel_price_change_annual = 0.1
    with caplog.at_level(logging.ERROR):
        present_value_of_changing_fuel_price = D1.present_value_of_changing_fuel_price(
            fuel_price, project_lifetime, wacc, crf, fuel_price_change_annual
        )
    assert (
        "This calculation is still faulty and you should check the resulting fuel price."
        in caplog.text
    ), f"An error message should be displayed to warn the user that using a `fuel_price_change_annual` is not recommended."
    exp = (fuel_price + fuel_price * (1 + fuel_price_change_annual) / (1 + wacc)) * crf
    assert (
        present_value_of_changing_fuel_price == exp
    ), f"The present value of the fuel price when there is an annual fuel price change was expected to be {exp} but is {present_value_of_changing_fuel_price}."
