#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Description of file

Name developers
"""

import os
import argparse

from auction_ABM.helpers.data import load_parameters

def set_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("name", type=str, help="name of the simulation to run")
    parser.add_argument("market_type", type=str, choices=["GS", "TD"], help="market type")
    parser.add_argument("market_id", type=int, help="id of market")
    args = parser.parse_args()

    if not do_files_exists(args.market_type, args.market_id, args.name):
        parser.error("cannot find files for simulation with name: {}".format(args.name))
    
    return args.name, args.market_type, args.market_id

def do_files_exists(market_type, market_id, name):
    """
    Checks if the files are present and correctyle named.
    """
    market_folder = "{}_market_{}".format(market_type, market_id)
    print(market_folder)
    folder = os.path.join(market_folder, name)
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