#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Description of file

Name developers
"""

import os
import sys
sys.path.insert(0, "auction_ABM")

import matplotlib.pyplot as plt

from helpers.cmd_cda import set_arguments
from helpers.data import load_demand_supply, load_parameters
from classes.auctions.cda_GS import CDA


if __name__ == "__main__":
    name, market_id = set_arguments()
    prices_buy, prices_sell, eq = load_demand_supply(name, market_id)
    params = load_parameters(name)
    params_strats, total_buyers_strats, total_sellers_strats, params_model = params

    auction = CDA(
        0, prices_buy, prices_sell, eq, params_model, params_strategies=params_strats, 
        total_buyers_strategies=total_buyers_strats, total_sellers_strategies=total_sellers_strats, 
        save_output=True
    )
    auction.run_model()

    data_model = auction.datacollector.get_model_vars_dataframe()
    print(data_model.head())
    data_model.plot(x="Time", y="Price")
    plt.show()
    plt.close()