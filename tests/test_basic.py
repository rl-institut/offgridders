import pytest
import os

from ..src.cli import main

def test_execution_not_terminated():
    answer = main(input_file=os.path.join("tests", "inputs", "pytest_test.xlsx"))
    assert answer == 1, f"Simulation with default inputs terminated."

'''
def test_blacks_main():
    # Testing code formatting in main folder
    r = os.system("black --check /src")
    assert r == 0, f"Black exited with:\n {r}"


def test_blacks_code_folder():
    # Testing code formatting in code folder
    r = os.system("black --check /tests")
    assert r == 0, f"Black exited with:\n {r}"
'''