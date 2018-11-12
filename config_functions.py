'''
Small scripts to keep the main file clean
'''

import pandas

from oemof.tools import logger
import logging

class config_func():
    def cases():
        from config import simulated_cases
        listof_cases = []
        for keys in simulated_cases:
            if simulated_cases[keys] == True: listof_cases.append(keys)

        str_cases_simulated = ''
        for item in listof_cases:
            str_cases_simulated = str_cases_simulated + item + ', '

        logging.info('The cases simulated are: ' + str_cases_simulated[:-2])
        return listof_cases

