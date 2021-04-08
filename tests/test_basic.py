import pytest
import os

from ..src.cli import main


def test_execution_not_terminated():
    answer = main(input_file=os.path.join("tests", "inputs", "pytest_test.xlsx"))
    assert answer == 1, f"Simulation with default inputs terminated."