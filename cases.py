'''
Overlying script for tool for the analysis of possible
operational modes of micro grids interconnecting with an unreliable national grid
'''

import os
import pandas

from oemof.tools import logger
import logging
# Logging
#logger.define_logging(logfile='main_tool.log',
#                      screen_level=logging.INFO,
#                      file_level=logging.DEBUG)

class cases():
    ###############################################################################
    # Dispatch with MG as sunk costs
    ###############################################################################
    def buyoff():
        logging.debug('            Simulation of case "buyoff" complete.')
        return

    ###############################################################################
    # Dispatch at parallel operation (mg as backup)
    ###############################################################################
    def parallel():
        logging.debug('            Simulation of case "parallel" complete.')
        return

    ###############################################################################
    # Dispatch with national grid as backup
    ###############################################################################
    def backupgrid():
        logging.debug('            Simulation of case "backupgrid" complete.')
        return

    ###############################################################################
    # Dispatch at buy from and sell to grid
    ###############################################################################
    def buysell():
        logging.debug('            Simulation of case "buysell" complete.')
        return

    ###############################################################################
    # Optimal adapted MG design and dispatch
    ###############################################################################
    def adapted():
        logging.debug('            Simulation of case "adapted" complete.')
        return

    ###############################################################################
    # Optimal mix and dispatch at interconnected state
    ###############################################################################
    def oem_interconnected():
        logging.debug('            Simulation of case "oem_interconnected" complete.')
        return

    ###############################################################################
    # Basecase
    ###############################################################################
    def base():
        logging.debug('            Simulation of case "base" complete.')
        return
    