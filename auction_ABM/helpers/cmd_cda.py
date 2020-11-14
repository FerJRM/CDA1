#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Description of file

Name developers
"""

import os
import argparse

CWD = os.getcwd()
DS = os.path.join(CWD, "data", "demand_and_supply")
PARAMS = os.path.join(CWD, "data", "parameters")

def set_arguments():
    """
    Set the necessary command-line arguments for cda.py
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "name", type=str, help="name of the simulation to run"
    )
    parser.add_argument(
        "market_id", type=int, help="id of market of the given simulation to to run"
    )
    
    args = parser.parse_args()
    if not do_files_exists(args.name, args.market_id):
        parser.error(
            "Cannot find appropriate data files for simulation with name: {} " \
            "and market id: {}".format(args.name, args.market_id)
            )

    return args.name, args.market_id

def do_files_exists(name, market_id):
    """
    Checks if the files are present and correctyle named.
    """
    ds_file = os.path.join(DS, name, "market_{}.txt".format(market_id))
    if not os.path.exists(ds_file):
        return False

    eq_file = os.path.join(DS, name, "equilibrium_market_{}.txt".format(market_id))
    if not os.path.exists(eq_file):
        return False

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