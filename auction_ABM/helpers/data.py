#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Description of file

Name developers
"""

import os

def load_demand_supply(market_name, market_id):
    """
    Loads demand and supply schedule from text file into lists
    """
    ds_folder = "{}_market_{}".format(market_name, market_id)
    ds_file = os.path.join(ds_folder, "market.txt".format(market_id))
    prices_buy, prices_sell = [], []
    with open(ds_file, 'r') as f:
        line = f.readline().rstrip("\n")
        line = f.readline().rstrip("\n")
        
        while line != "":
            buy, sell = line.split("\t")
            prices_buy.append(int(buy)), prices_sell.append(int(sell))
            line = f.readline().rstrip("\n")

    eq_file = os.path.join(ds_folder, "equilibrium_market.txt".format(market_id))
    eq = []
    with open(eq_file, 'r') as f:
        for line in f:
            if "\t" in line:
                _, value = line.rstrip("\n").split("\t")
                if "." in value:
                    eq.append(float(value))
                else:
                    eq.append(int(value))

    return prices_buy, prices_sell, eq

def load_parameters(market_name, market_id, name):
    """
    Load model parameters for a simulation in a double auction with a 
    certain distribution of agents, their corresponding parameters and thus
    also auction parameters.
    """
    # folder = os.path.join("data", "parameters", name)
    folder = os.path.join("{}_market_{}".format(market_name, market_id), name)
    distr_file = os.path.join(folder, "distribution_agents.txt")
    agents_file = os.path.join(folder, "parameters_agents.txt")
    auction_file = os.path.join(folder, "parameters_CDA.txt")

    params_strategies = {}
    with open(agents_file, 'r') as f:
        strategy = ""
        for line in f:
            if "=" not in line and line != "\n":
                strategy = line.rstrip("\n")
                params_strategies[strategy.upper()] = {}
            elif "=" in line:
                line = line.rstrip("\n")
                param, value = line.split("=")
                if "," not in value:
                    params_strategies[strategy.upper()][param] = float(value)
                else:
                    value_tuple = tuple(float(x.strip()) for x in value.split(","))
                    params_strategies[strategy.upper()][param] = value_tuple

    total_buyers_strategies, total_sellers_strategies = {}, {}
    with open(distr_file, 'r') as f:
        strategy = ""
        for line in f:
            if "=" not in line and line != "\n":
                strategy = line.rstrip("\n")
            elif "=" in line and "buyers" in line:
                line = line.rstrip("\n")
                _, buyers = line.split("=")
                total_buyers_strategies[strategy.upper()] = int(buyers)
            elif "=" in line and "sellers" in line:
                line = line.rstrip("\n")
                _, sellers = line.split("=")
                total_sellers_strategies[strategy.upper()] = int(sellers)

    model_params = {}
    with open(auction_file, 'r') as f:
        for line in f:
            if "=" in line:
                param, value = line.rstrip("\n").split("=")
                if "." in value:
                    model_params[param] = float(value)
                else:
                    model_params[param] = int(value)

    return params_strategies, total_buyers_strategies, total_sellers_strategies, model_params
