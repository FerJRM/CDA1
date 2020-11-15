#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Description of file

Name developers
"""

import sys
sys.path.insert(0, "auction_ABM")

import matplotlib.pyplot as plt

from helpers.cmd_cda import set_arguments
from helpers.data import load_demand_supply, load_parameters
from classes.runners.cda_runner import CDARunner

if __name__ == "__main__":

    # retrieve command-line arguments, load demand and supply schedule 
    # and parameters model
    name, market_id, N, save_output, log = set_arguments()
    prices_buy, prices_sell, eq = load_demand_supply(name, market_id)
    params = load_parameters(name)
    params_strats, total_buyers_strats, total_sellers_strats, params_model = params
    cda_params = (
        name, market_id, prices_buy, prices_sell, eq, params_model, params_strats, 
        total_buyers_strats, total_sellers_strats, save_output, log
    )

    cda_run = CDARunner(name, N, cda_params, save_output=save_output)
    cda_run.run_all()

    # # plot price convergence for each period
    # data_periods = data_model.groupby("Period")
    # fig, axes = plt.subplots(ncols=data_periods.ngroups, sharey=True, figsize=(12,3))
    # for i, (period, d) in enumerate(data_periods):
    #     ax = d.plot(x="Time", y="Price", ax=axes[i], title="Period {}".format(i + 1))
    #     ax.legend().remove()
    # fig.tight_layout()
    # plt.show()
    # plt.close()