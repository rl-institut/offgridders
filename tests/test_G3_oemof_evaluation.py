import pandas as pd
import numpy as np
from pandas.util.testing import assert_series_equal

import src.G3_oemof_evaluate as G3
from src.constants import EVALUATED_DAYS, GENSET_HOURS_OF_OPERATION


def test_get_hours_of_operation():
    genset_generation = pd.Series([0, 0, 0, 0.5, 2])
    oemof_results = {}
    case_dict = {EVALUATED_DAYS: 5}
    operation_boolean = G3.get_hours_of_operation(
        oemof_results, case_dict, genset_generation
    )
    exp = pd.Series([0, 0, 0, 1, 1])
    assert (
        operation_boolean.sum() == 2
    ), f"It was expected that the number of operation hours in the evaluated timeframe was 2, but it is {operation_boolean.sum()}."
    assert_series_equal(
        genset_generation.astype(np.float64), exp(np.float64), check_names=False,
    ), f"The operational hours pd.Series should be the same when calculated with the function to the expected series."
    assert (
        GENSET_HOURS_OF_OPERATION in oemof_results
    ), f"Parameter {GENSET_HOURS_OF_OPERATION} is not in the oemof_results, but was expected."
    assert oemof_results[GENSET_HOURS_OF_OPERATION] == 2 * (
        365 / 5
    ), f"Parameter {GENSET_HOURS_OF_OPERATION} is not of expected annual value {2*365/5}, but {oemof_results[GENSET_HOURS_OF_OPERATION]}."
