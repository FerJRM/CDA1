#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Description of file

Name developers
"""

import os
import argparse

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
    parser.add_argument(
        "cda_type", type=str, choices=["GS", "GS evo", "TD"], help="type of cda market to run"
    )
    parser.add_argument(
        "N", type=int, help="amount of simulations"
    )
    parser.add_argument(
        "--save_output", type=str2bool, default=False, help="save data transaction or not (default=True)"
    )
    parser.add_argument(
        "--log", type=str2bool, default=False, help="run with logfile or not (default=True)"
    )
    
    args = parser.parse_args()

    market_name = ""
    if "gs" in args.cda_type.lower():
        market_name = "GS"
    elif "td" in args.cda_type.lower():
        market_name = "TD"

    if not do_files_exists(args.name, market_name, args.market_id):
        parser.error(
            "Cannot find appropriate data files for simulation with name: {} " \
            "and market id: {}".format(args.name, args.market_id)
            )

    return args.name, market_name, args.market_id, args.cda_type, args.N, args.save_output, args.log

def str2bool(v):
    """
    Parser helper function for boolean type
    https://stackoverflow.com/questions/15008758/parsing-boolean-values-with-argparse
    """
    if isinstance(v, bool):
       return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

def do_files_exists(name, market_name, market_id):
    """
    Checks if the files are present and correctyle named.
    """
    market_folder = os.path.join("{}_market_{}".format(market_name, market_id))
    ds_file = os.path.join(market_folder, "market.txt")
    if not os.path.exists(ds_file):
        return False

    eq_file = os.path.join(market_folder, "equilibrium_market.txt")
    if not os.path.exists(eq_file):
        return False

    params_folder = os.path.join(market_folder, name)
    distr_file = os.path.join(params_folder, "distribution_agents.txt")
    if not os.path.exists(distr_file):
        return False

    agents_file = os.path.join(params_folder, "parameters_agents.txt")
    if not os.path.exists(agents_file):
        return False

    auction_file = os.path.join(params_folder, "parameters_CDA.txt")
    if not os.path.exists(auction_file):
        return False

    return True