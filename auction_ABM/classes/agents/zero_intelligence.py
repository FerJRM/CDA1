#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Description of file

Name developers
"""

from mesa import Agent

class ZI_buy(Agent):
    """
    An Zero Intelligence Constrained agent as described by Gode & Sunder (1993).
    Note, it acts as a buyer in a double auction
    """
    def __init__(self, unique_id, model, prices):
        super().__init__(unique_id, model)
        self.prices = prices
        self.idx_price = 0
        self.quantity = 0
        self.budget = sum(prices)

    def step(self):
        """
        Perform one action (step) in the auction for the agent
        """
        print(self.unique_id)

class ZI_sell(Agent):
    """
    An Zero Intelligence Constrained agent as described by Gode & Sunder (1993).
    Note, it acts as a seller in a double auction
    """
    def __init__(self, unique_id, model, prices):
        super().__init__(unique_id, model)
        self.prices = prices
        self.idx_price = 0
        self.quantity = len(prices)
        self.budget = 0

    def step(self):
        """
        Perform one action (step) in the auction for the agent
        """
        print(self.unique_id)

# class ZI_C(Agent):
#     """
#     An Zero Intelligence Constrained agent as described by Gode & Sunder (1993)
#     """
#     def __init__(self, unique_id, model, side, prices):
#         super().__init__(unique_id, model)
#         self.side = side
#         self.prices = prices

#         self.commodities = len(prices) if side == "seller" else 