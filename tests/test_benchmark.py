import pytest
import os
import logging

from ..Offgridders import main
from src.constants import PYTEST_FOLDER

BENCHMARK_TEST_FOLDER = "benchmark_tests"

def test_benchmark_OffsetGenerator(caplog):
    """The input file defines two cases: One diesel generator with fix efficiency which is to be optimized, and diesel
    generator with efficiency curve and minimal loading whose capacity is defined by the first optimization."""
    benchmark_test_file = os.path.join(
        PYTEST_FOLDER, BENCHMARK_TEST_FOLDER, "generator_with_efficiency_curve.xlsx"
    )

    answer = main(input_file=benchmark_test_file)
    assert answer == 1, f"The simulation terminated for the different combinations of input files."