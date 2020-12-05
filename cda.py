#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Description of file

Name developers
"""

import matplotlib.pyplot as plt

from auction_ABM.helpers.cmd_cda import set_arguments
from auction_ABM.helpers.data import load_demand_supply, load_parameters
from auction_ABM.runners.cda_runner import CDARunner

if __name__ == "__main__":

    # retrieve command-line arguments, load demand and supply schedule 
    # and parameters model
    name, market_id, cda_type, N, save_output, log = set_arguments()
    prices_buy, prices_sell, eq = load_demand_supply(name, market_id)
    params = load_parameters(name)
    params_strats, total_buyers_strats, total_sellers_strats, params_model = params
    cda_params = (
        name, market_id, prices_buy, prices_sell, eq, params_model, params_strats, 
        total_buyers_strats, total_sellers_strats, save_output, log
    )

    cda_run = CDARunner(name, cda_type, N, cda_params, save_output=save_output)
    cda_run.run_all()