#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Description of file

Name developers
"""

import os
import argparse

from helpers.data import load_parameters

CWD = os.getcwd()
PARAMS = os.path.join(CWD, "data", "parameters")

def set_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("name", type=str, help="name of the simulation to run")
    parser.add_argument("market_id", type=int, help="id of market")
    args = parser.parse_args()

    if not do_files_exists(args.name):
        parser.error("cannot find files for simulation with name: {}".format(name))
    
    return args.name, args.market_id

def do_files_exists(name):
    """
    Checks if the files are present and correctyle named.
    """
    folder = os.path.join(PARAMS, name)
    distr_file = os.path.join(folder, "distribution_agents.txt")
    if not os.path.exists(distr_file):
        return False

    agents_file = os.path.join(folder, "parameters_agents.txt")
    if not os.path.exists(agents_file):
        return False

    auction_file = os.path.join(folder, "parameters_CDA.txt")
    if not os.path.exists(auction_file):
        return False

    return True