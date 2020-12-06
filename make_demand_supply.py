#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Description of file

Name developers
"""

import os

from auction_ABM.helpers.cmd_ds import set_arguments
from auction_ABM.helpers.data import load_parameters
import auction_ABM.helpers.demand_and_supply as ds

if __name__ == "__main__":
    name, market_type, market_id = set_arguments()
    params = load_parameters(market_type, market_id, name)
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

    ds.save_prices(prices_buy, prices_sell, equilibrium, market_type, market_id)

    ds.plot_demand_supply(
        prices_buy, prices_sell, all_prices_buy, all_prices_sell, 
        total_buyers, total_sellers, params_model["commodities"], 
        params_model["min_price"], params_model["max_price"], 
        market_type, market_id, True, True
    )