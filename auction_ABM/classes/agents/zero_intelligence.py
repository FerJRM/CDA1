#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Description of file

Name developers
"""

import math
import random

from mesa import Agent

class BasicAgent(Agent):
    market_side = "None"
    strategy = "None"

    def __init__(self, unique_id, model, prices, eq_surplus):
        super().__init__(unique_id, model)
        self.prices = prices
        self.quantity = 0
        self.budget = sum(prices)
        self.eq_surplus = eq_surplus
        self.surplus = 0
        self.profit_dispersion = 0
        self.offer = 0
        self.in_market = True
        self.active = True
        
    def get_info(self):
        """
        Returns a formatted string containing the current state of agent
        """
        return f"==============================================" \
            f"\nID: {self.unique_id} " \
            f"\nAgent: {self.strategy} " \
            f"\nSide: {self.market_side} " \
            f"\nValuation: {self.prices[self.quantity]} " \
            f"\nOffer: {self.offer} " \
            f"\nQuantity: {self.quantity} " \
            f"\nBudget: {self.budget}" \
            f"\n================================================="

    def still_commodities(self):
        """
        Returns True if agent still has commodites left, otherwise False
        """
        return self.quantity < len(self.prices)

    def set_in_market(self):
        """
        Determines if trader is still in market (not all commodies )
        """
        self.in_market = self.still_commodities()

    def is_in_market(self):
        """
        Returns True if activate in auction, otherwise False
        """
        return self.in_market

    def set_activity(self):
        """
        Determines if buyer is active (can shout price)
        """
        self.active = True

    def is_active(self):
        """
        Checks if buyer can make offer thats within budget contraint and
        without losses
        """
        return self.active

    def get_price(self):
        """
        Get current limit price
        """
        if self.still_commodities():
            return self.prices[self.quantity]
        
        return 0

    def get_budget(self):
        """
        Get budget.
        """
        return self.budget

    def set_profit_dispersion(self):
        """
        """
        self.profit_dispersion = (self.surplus - self.eq_surplus) ** 2

    def offer_price(self):
        """
        Shouts price.
        """
        self.offer = 0

    def transaction_update(self, price):
        """
        Update surplus, quantity bought, budget and price index for a certain
        transaction price
        """
        return 0

    def reset_offer(self):
        """
        Reset offer to initial value.
        """
        self.offer = 0

    def reset_agent(self):
        """
        Resets attributes agents to initial values
        """
        self.quantity = 0
        self.budget = sum(self.prices)
        self.offer = 0
        self.surplus = 0
        self.in_market = True
        self.active = True

    def step(self):
        """
        Perform one action (step) in the auction for the agent
        """
        pass
    
class ZI_buy(BasicAgent):
    """
    An Zero Intelligence Constrained agent as described by Gode & Sunder (1993).
    Note, it acts as a buyer in a double auction
    """
    market_side = "buyer"
    strategy = "ZI"

    def set_in_market(self):
        """
        Determines if trader is still in market (not all commodies )
        """
        self.in_market = self.still_commodities()

    def set_activity(self):
        """
        Checks if buyer can make offer thats within budget contraint and
        without losses
        """
        if self.still_commodities(): 
            is_endowed =  self.prices[self.quantity] > self.model.best_bid
            enough_budget = self.model.best_bid < self.budget
            self.active = is_endowed and enough_budget
        else:
            self.active = False

    def offer_price(self):
        """
        Generates a random bod between the limit price/budget and current best bid
        """
        valuation = self.prices[self.quantity]
        max_bid = valuation if self.budget > valuation else self.budget
        self.offer = random.randint(self.model.best_bid + 1, max_bid)

    def transaction_update(self, price):
        """
        Update surplus, quantity bought, budget and price index for a certain
        transaction price
        """
        surplus = self.prices[self.quantity] - price
        self.surplus += surplus
        self.budget -= price
        self.quantity += 1

        return surplus

    def step(self):
        """
        Perform one action (step) in the auction for the agent
        """
        self.offer_price()

class ZI_sell(BasicAgent):
    """
    An Zero Intelligence Constrained agent as described by Gode & Sunder (1993).
    Note, it acts as a seller in a double auction
    """
    market_side = "seller"
    strategy = "ZI"

    def __init__(self, unique_id, model, prices, eq_surplus):
        super().__init__(unique_id, model, prices, eq_surplus)
        self.budget = 0
        self.offer = math.inf

    def get_price(self):
        if self.still_commodities():
            return self.prices[self.quantity]

        return math.inf

    def set_activity(self):
        if self.still_commodities():
            self.active = self.prices[self.quantity] < self.model.best_ask
        else:
            self.active = False

    def offer_price(self):
        valuation = self.prices[self.quantity]
        if self.model.best_ask == math.inf:
            self.offer = random.randint(valuation, self.model.max_poss_price)
        else:
            self.offer = random.randint(valuation, self.model.best_ask - 1)

    def transaction_update(self, price):
        """
        Update surplus, quantity bought, budget and price index for a certain
        transaction price
        """
        surplus = price - self.prices[self.quantity]
        self.surplus += surplus
        self.budget += price
        self.quantity += 1

        return surplus

    def reset_offer(self):
        """
        Reset offer to initial value.
        """
        self.offer = math.inf

    def reset_agent(self):
        """
        Resets attributes agents to initial values
        """
        self.quantity = 0
        self.budget = 0
        self.offer = math.inf
        self.surplus = 0
        self.in_market = True
        self.active = True

    def step(self):
        """
        Perform one action (step) in the auction for the agent
        """
        self.offer_price()