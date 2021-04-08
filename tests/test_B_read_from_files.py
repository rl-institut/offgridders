import logging

import src.B_read_from_files as B
from src.constants import (
    GENSET_WITH_EFFICIENCY_CURVE,
    CAPACITY_GENSET_KW,
    OEM,
    GENSET_WITH_MINIMAL_LOADING,
    PEAK_DEMAND,
)


def test_process_generator_settings_missing_new_parameter(caplog):
    test_dict = {CAPACITY_GENSET_KW: OEM, GENSET_WITH_MINIMAL_LOADING: True}
    with caplog.at_level(logging.WARNING):
        B.process_generator_settings(case_definition=test_dict, case="case")
    assert (
        B.MISSING_PARAMETER_WARNING in caplog.text
    ), f"A warning message that a parameter is missing should be displayed."


def test_process_generator_settings_no_generator(caplog):
    test_dict = {
        CAPACITY_GENSET_KW: None,
        GENSET_WITH_MINIMAL_LOADING: True,
        GENSET_WITH_EFFICIENCY_CURVE: True,
    }
    with caplog.at_level(logging.DEBUG):
        B.process_generator_settings(case_definition=test_dict, case="case")
    assert (
        " does not include a generator." in caplog.text
    ), f"No generator is in the system, but it seems that this is not recognized."


def test_process_generator_settings_peak_demand_sized_generator_fix_eff_no_minload(
    caplog,
):
    test_dict = {
        CAPACITY_GENSET_KW: PEAK_DEMAND,
        GENSET_WITH_MINIMAL_LOADING: False,
        GENSET_WITH_EFFICIENCY_CURVE: False,
    }
    with caplog.at_level(logging.DEBUG):
        B.process_generator_settings(case_definition=test_dict, case="case")
    assert (
        "has a generator with fixed capacity" in caplog.text
    ), f"If the generator is of fix capacity predetermined by {PEAK_DEMAND}, all generator types can be used for the simulation."


def test_process_generator_settings_peak_demand_sized_generator_fix_eff_with_minload(
    caplog,
):
    test_dict = {
        CAPACITY_GENSET_KW: PEAK_DEMAND,
        GENSET_WITH_MINIMAL_LOADING: True,
        GENSET_WITH_EFFICIENCY_CURVE: False,
    }
    with caplog.at_level(logging.DEBUG):
        B.process_generator_settings(case_definition=test_dict, case="case")
    assert (
        "has a generator with fixed capacity" in caplog.text
    ), f"If the generator is of fix capacity predetermined by {PEAK_DEMAND}, all generator types can be used for the simulation."


def test_process_generator_settings_peak_demand_sized_generator_var_eff_no_minload(
    caplog,
):
    test_dict = {
        CAPACITY_GENSET_KW: PEAK_DEMAND,
        GENSET_WITH_MINIMAL_LOADING: False,
        GENSET_WITH_EFFICIENCY_CURVE: True,
    }
    with caplog.at_level(logging.DEBUG):
        B.process_generator_settings(case_definition=test_dict, case="case")
    assert (
        "has a generator with fixed capacity" in caplog.text
    ), f"If the generator is of fix capacity predetermined by {PEAK_DEMAND}, all generator types can be used for the simulation."

    with caplog.at_level(logging.WARNING):
        B.process_generator_settings(case_definition=test_dict, case="case")
    assert (
        B.NO_MINIMAL_LOADING_WITH_OFFSET_TRANSFORMER in caplog.text
    ), f"If the generator is of fix capacity predetermined by {PEAK_DEMAND}, all generator types can be used for the simulation. Here, the efficiency curve is used but not the minload, so a warning message should be displayed: {B.NO_MINIMAL_LOADING_WITH_OFFSET_TRANSFORMER}"


def test_process_generator_settings_peak_demand_sized_generator_var_eff_with_minload(
    caplog,
):
    test_dict = {
        CAPACITY_GENSET_KW: PEAK_DEMAND,
        GENSET_WITH_MINIMAL_LOADING: True,
        GENSET_WITH_EFFICIENCY_CURVE: True,
    }
    with caplog.at_level(logging.DEBUG):
        B.process_generator_settings(case_definition=test_dict, case="case")
    assert (
        "has a generator with fixed capacity" in caplog.text
    ), f"If the generator is of fix capacity predetermined by {PEAK_DEMAND}, all generator types can be used for the simulation."


def test_process_generator_settings_generator_to_be_optimized_fix_eff_no_minload(
    caplog,
):
    test_dict = {
        CAPACITY_GENSET_KW: OEM,
        GENSET_WITH_MINIMAL_LOADING: False,
        GENSET_WITH_EFFICIENCY_CURVE: False,
    }
    with caplog.at_level(logging.DEBUG):
        B.process_generator_settings(case_definition=test_dict, case="case")
    assert (
        "should be optimized." in caplog.text
    ), f"A message should be shown that this generator is supposed to be optimized."


def test_process_generator_settings_generator_to_be_optimized_fix_eff_with_minload(
    caplog,
):
    test_dict = {
        CAPACITY_GENSET_KW: OEM,
        GENSET_WITH_MINIMAL_LOADING: True,
        GENSET_WITH_EFFICIENCY_CURVE: False,
    }
    with caplog.at_level(logging.DEBUG):
        B.process_generator_settings(case_definition=test_dict, case="case")
    assert (
        "should be optimized." in caplog.text
    ), f"A message should be shown that this generator is supposed to be optimized."

    with caplog.at_level(logging.WARNING):
        B.process_generator_settings(case_definition=test_dict, case="case")
    assert (
        B.OPTIMIZATION_NOT_POSSIBLE_MINLOAD_OEM in caplog.text
    ), f"This warning message should be displayed: {B.OPTIMIZATION_NOT_POSSIBLE_MINLOAD_OEM}"


def test_process_generator_settings_generator_to_be_optimized_var_eff_with_minload(
    caplog,
):
    test_dict = {
        CAPACITY_GENSET_KW: OEM,
        GENSET_WITH_MINIMAL_LOADING: True,
        GENSET_WITH_EFFICIENCY_CURVE: True,
    }
    with caplog.at_level(logging.DEBUG):
        B.process_generator_settings(case_definition=test_dict, case="case")
    assert (
        "should be optimized." in caplog.text
    ), f"A message should be shown that this generator is supposed to be optimized."
    with caplog.at_level(logging.ERROR):
        B.process_generator_settings(case_definition=test_dict, case="case")
    assert (
        B.OPTIMIZATION_NOT_POSSIBLE_OFFSET_TRANSFORMER_OEM in caplog.text
    ), f"This warning message should be displayed: {B.OPTIMIZATION_NOT_POSSIBLE_OFFSET_TRANSFORMER_OEM}"


def test_process_generator_settings_generator_to_be_optimized_var_eff_no_minload(
    caplog,
):
    test_dict = {
        CAPACITY_GENSET_KW: OEM,
        GENSET_WITH_MINIMAL_LOADING: False,
        GENSET_WITH_EFFICIENCY_CURVE: True,
    }
    with caplog.at_level(logging.DEBUG):
        B.process_generator_settings(case_definition=test_dict, case="case")
    assert (
        "should be optimized." in caplog.text
    ), f"A message should be shown that this generator is supposed to be optimized."
    with caplog.at_level(logging.ERROR):
        B.process_generator_settings(case_definition=test_dict, case="case")
    assert (
        B.OPTIMIZATION_NOT_POSSIBLE_OFFSET_TRANSFORMER_OEM in caplog.text
    ), f"This warning message should be displayed: {B.OPTIMIZATION_NOT_POSSIBLE_OFFSET_TRANSFORMER_OEM}"
