#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Description of file

Name developers
"""

import os
import sys
sys.path.insert(0, "auction_ABM")

from helpers.cmd_ds import set_arguments
from helpers.data import load_parameters
import helpers.demand_and_supply as ds

DS_PLOT = os.path.join("results", "demand_and_supply")
DS_DATA = os.path.join("data", "demand_and_supply")

if __name__ == "__main__":
    name, market_id = set_arguments()
    params = load_parameters(name)
    params_strats, total_buyers_strats, total_sellers_strats, params_model = params

    total_buyers, total_sellers = 0, 0
    for buyers, sellers in zip(total_buyers_strats.values(), total_sellers_strats.values()):
        total_buyers += buyers
        total_sellers += sellers

    ds_results = ds.generate_random_DS(
        params_model["min_price"], params_model["max_price"], 
        total_buyers, total_sellers,
        params_model["commodities"]
    )
    prices_buy, prices_sell, all_prices_buy, all_prices_sell, equilibrium = ds_results

    folder = os.path.join(DS_DATA, name)
    ds.save_prices(prices_buy, prices_sell, equilibrium, folder, market_id)

    folder = os.path.join(DS_PLOT, name)
    ds.plot_demand_supply(
        prices_buy, prices_sell, all_prices_buy, all_prices_sell, 
        total_buyers, total_sellers, params_model["commodities"], 
        params_model["min_price"], params_model["max_price"], 
        folder, market_id, True, True
    )