#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Description of file

Name developers
"""

import os
import sys
import logging
sys.path.insert(0, "auction_ABM")

import matplotlib.pyplot as plt

from helpers.cmd_cda import set_arguments
from helpers.data import load_demand_supply, load_parameters
from classes.auctions.cda_GS import CDA

RESULTS = os.path.join("results")

if __name__ == "__main__":
    name, market_id, log = set_arguments()
    prices_buy, prices_sell, eq = load_demand_supply(name, market_id)
    params = load_parameters(name)
    params_strats, total_buyers_strats, total_sellers_strats, params_model = params

    if log:
        folder = os.path.join("results", "log", name)
        os.makedirs(folder, exist_ok=True)
        log_file = os.path.join(folder, "market_{}.log".format(market_id))
        logging.basicConfig(filename=log_file, filemode='w', level=logging.DEBUG)
        logging.info("Start log file of {} market {}".format(name, market_id))

    auction = CDA(
        0, prices_buy, prices_sell, eq, params_model, params_strategies=params_strats, 
        total_buyers_strategies=total_buyers_strats, total_sellers_strategies=total_sellers_strats, 
        save_output=True, log=log
    )
    auction.run_model()

    data_model = auction.datacollector.get_model_vars_dataframe()
    print(data_model.head())

    data_periods = data_model.groupby("Period")
    fig, axes = plt.subplots(ncols=data_periods.ngroups, sharey=True, figsize=(12,3))
    for i, (period, d) in enumerate(data_periods):
        ax = d.plot(x="Time", y="Price", ax=axes[i], title="Period {}".format(i + 1))
        ax.legend().remove()
    # data_model.plot(x="Time", y="Price")
    fig.tight_layout()
    plt.show()
    plt.close()