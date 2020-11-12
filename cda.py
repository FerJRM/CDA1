#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Description of file

Name developers
"""

import os
import sys
sys.path.insert(0, "auction_ABM")

import helpers.demand_and_supply as ds


if __name__ == "__main__":
    min_poss_price, max_poss_price = 0, 200
    min_limit, max_limit, total_buyers, total_sellers, commodities = 1, 200, 10, 10, 10

    # data_ds = os.path.join("data", "demand_and_supply", "random", "market_1.txt")
    # prices_buy, prices_sell = ds.load_demand_supply(data_ds)

    ds_results = ds.generate_random_DS(min_limit, max_limit, total_buyers, total_sellers, commodities)
    prices_buy, prices_sell, all_prices_buy, all_prices_sell, equilibrium = ds_results
    p_eq, q_eq, surplus = equilibrium
    print("Equilibrium price:", p_eq)
    print("Equilibrium quantity:", q_eq)
    print("===============================================================")

    folder = os.path.join("results", "demand_and_supply", "random")
    ds.plot_demand_supply(
        prices_buy, prices_sell, all_prices_buy, all_prices_sell, 
        total_buyers, total_sellers, commodities, min_poss_price, max_poss_price, 
        folder, 1, False, True
    )

    folder = os.path.join("data", "demand_and_supply", "random")
    ds.save_prices(prices_buy, prices_sell, equilibrium, folder, 1)