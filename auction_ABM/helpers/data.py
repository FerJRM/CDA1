#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Description of file

Name developers
"""

import os

def load_demand_supply(name, market_id):
    """
    Loads demand and supply schedule from text file into lists
    """
    ds_file = os.path.join("data", "demand_and_supply", name, "market_{}.txt".format(market_id))
    prices_buy, prices_sell = [], []
    with open(ds_file, 'r') as f:
        line = f.readline().rstrip("\n")
        line = f.readline().rstrip("\n")
        
        while line != "":
            buy, sell = line.split("\t")
            prices_buy.append(int(buy)), prices_sell.append(int(sell))
            line = f.readline().rstrip("\n")

    eq_file = os.path.join(
        "data", "demand_and_supply", name, "equilibrium_market_{}.txt".format(market_id)
    )
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

def load_parameters(name):
    """
    Load model parameters for a simulation in a double auction with a 
    certain distribution of agents, their corresponding parameters and thus
    also auction parameters.
    """
    folder = os.path.join("data", "parameters", name)
    distr_file = os.path.join(folder, "distribution_agents.txt")
    agents_file = os.path.join(folder, "parameters_agents.txt")
    auction_file = os.path.join(folder, "parameters_CDA.txt")

    params_strategies = {}
    with open(agents_file, 'r') as f:
        strategy = ""
        for line in f:
            if "=" not in line and line != "\n":
                strategy = line.rstrip("\n")
                params_strategies[strategy] = {}
            elif "=" in line:
                line = line.rstrip("\n")
                param, value = line.split("=")
                params_strategies[strategy][param] = float(value)

    total_buyers_strategies, total_sellers_strategies = {}, {}
    with open(distr_file, 'r') as f:
        strategy = ""
        for line in f:
            if "=" not in line and line != "\n":
                strategy = line.rstrip("\n")
            elif "=" in line and "buyers" in line:
                line = line.rstrip("\n")
                _, buyers = line.split("=")
                total_buyers_strategies[strategy] = int(buyers)
            elif "=" in line and "sellers" in line:
                line = line.rstrip("\n")
                _, sellers = line.split("=")
                total_sellers_strategies[strategy] = int(sellers)

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
