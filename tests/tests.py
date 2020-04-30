import pytest
import os

from ..A0_main_script import main


def test_execution_not_terminated():
    assert main() == 1


def test_blacks_main():
    # Testing code formatting in main folder
    r = os.system("black --check *.py")
    assert r == 0


def test_blacks_code_folder():
    # Testing code formatting in code folder
    r = os.system("black --check code_folder/*.py")
    assert r == 0
