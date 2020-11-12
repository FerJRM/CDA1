#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Description of file

Name developers
"""

import math
from collections import defaultdict

from mesa import Model
from mesa.time import RandomActivation

class CDA(Model):
    """
    Continuous Double Auction model as represented in Gode en Sunder (1993).
    It manages the flow in of agents steps and collects the necessary data,
    """
    def __init__(
            self, prices_buy, prices_sell, equilibrium, min_poss_price, 
            max_poss_price, periods=5, total_time=300, strategies=["ZI"], 
            params_strategies=[{}], total_buyers_strategies=[10], 
            total_sellers_strategies=[10], save_output=False
        ):
        
        self.prices_buy = prices_buy
        self.prices_sell = prices_sell
        self.eq_price, self.eq_quantity, self.eq_surplus = equilibrium
        self.min_poss_price = min_poss_price
        self.max_poss_price = max_poss_price

        self.periods = periods
        self.total_time = total_time
        self.time = 0

        self.total_buyers_auction = 0
        for total_buyers in total_buyers_strategies:
            self.total_buyers_auction += total_buyers

        self.total_sellers_auction = 0
        for total_sellers in total_sellers_strategies:
            self.total_sellers_auction += total_sellers

        self.save_output = save_output

        # monitoring variables for during a trading period
        self.best_bid, self.best_bid_id = 0, None
        self.best_ask, self.best_ask_id = math.inf, None
        self.surplus = defaultdict(float)
        self.quantity = defaultdict(float)


        # set up scheduler for auction
        self.schedule = RandomActivation(self)
        # intialize population and datacollector?