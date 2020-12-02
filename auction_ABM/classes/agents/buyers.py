#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Description of file

Name developers
"""

import math
import random

from mesa import Agent

class ZI_buy(Agent):
    market_side = "buyer"
    strategy = "ZI"

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
        self.can_shout = True
        self.no_transactions = 0

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
        self.active = self.model.best_bid < self.model.max_poss_price

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

    def reset_no_transactions(self):
        """
        Resets the number of steps in which no transactions occur
        """
        self.no_transactions = 0

    def update_no_transactions(self):
        """
        Updates the numbers of steps with no transaction
        """
        self.no_transactions += 1

    def set_profit_dispersion(self):
        """
        """
        self.profit_dispersion = (self.surplus - self.eq_surplus) ** 2

    def offer_price(self):
        """
        Shouts price.
        """
        self.offer = random.randint(self.model.best_bid + 1, self.model.max_poss_price)

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
        self.no_transactions = 0

    def step(self):
        """
        Perform one action (step) in the auction for the agent
        """
        self.offer_price()
    
class ZI_C_buy(ZI_buy):
    """
    An Zero Intelligence Constrained agent as described by Gode & Sunder (1993).
    Note, it acts as a buyer in a double auction
    """
    market_side = "buyer"
    strategy = "ZI_C"

    def willing_to_shout(self):
        """
        Determines if the buyer is willing to shout
        """
        is_endowed =  self.prices[self.quantity] > self.model.best_bid
        enough_budget = self.model.best_bid < self.budget
        self.can_shout = is_endowed and enough_budget

    def set_activity(self):
        """
        Checks if buyer can make offer thats within budget contraint and
        without losses
        """
        if self.still_commodities():
            self.willing_to_shout()
            self.active = self.can_shout
        else:
            self.active = False

    def offer_price(self):
        """
        Generates a random bod between the limit price/budget and current best bid
        """
        valuation = self.prices[self.quantity]
        max_bid = valuation if self.budget > valuation else self.budget
        self.offer = random.randint(self.model.best_bid + 1, max_bid)

class Kaplan_buy(ZI_C_buy):
    """
    Implementation of an Kaplan agent (Rust, Palm & Miller, 1993)
    """
    market_side = "buyer"
    strategy = "KAPLAN"

    def __init__(self, unique_id, model, prices, eq_surplus, params):
        super().__init__(unique_id, model, prices, eq_surplus)
        self.spread_ratio = params["spread_ratio"]
        self.profit_perc = params["profit_perc"]
        self.time_frac = params["time_frac"]
        self.most = None
        self.can_shout = False
        self.juicy_offer = False
        self.small_spread = False
        self.time_out = False
        self.truthtelling = False

    def get_info(self):
        """
        Returns a formatted string containing the current state of agent
        """
        return f"==============================================" \
            f"\nID: {self.unique_id} " \
            f"\nAgent: {self.strategy} " \
            f"\nSide: {self.market_side} " \
            f"\nValuation: {self.prices[self.quantity]} " \
            f"\nQuantity: {self.quantity} " \
            f"\nBudget: {self.budget}" \
            f"\nOffer: {self.offer} " \
            f"\nTime fraction: {self.time_frac}" \
            f"\nSpread ratio: {self.spread_ratio}" \
            f"\nProfit percentage: {self.profit_perc}" \
            f"\nCan shout: {self.can_shout}" \
            f"\nJuicy offer: {self.juicy_offer}" \
            f"\nSmall spread: {self.small_spread}" \
            f"\nTime out: {self.time_out}" \
            f"\nTruthtelling mode: {self.truthtelling}" \
            f"\nMost: {self.most}" \
            f"\n================================================="

    def willing_to_shout(self):
        """
        Determines if the buyer is willing to shout
        """
        best_ask = self.model.best_ask
        if self.quantity != len(self.prices) - 1:
            next_token = self.prices[self.quantity + 1]
        else:
            next_token = self.prices[self.quantity]

        if best_ask != math.inf:
            self.most = min(best_ask, next_token - 1)
        else:
            self.most = next_token - 1

        is_better_bid = self.most > self.model.best_bid
        is_endowed =  self.prices[self.quantity] >= self.most
        enough_budget = self.most <= self.budget
        # self.can_shout = is_better_bid and is_endowed and enough_budget
        return is_better_bid and is_endowed and enough_budget     

    def is_juicy_offer(self):
        """
        Determines if the best ask is less than the minimum trade price trade 
        price in the previous period.
        """
        # self.juicy_offer = self.model.best_ask < self.model.prev_min_trade
        return self.model.best_ask < self.model.prev_min_trade

    def is_small_spread(self):
        """
        Determines if reasonalbe offer has been made, bid-ask spread is small enough
        and the expected profit is sufficient.
        """
        reasonable_offer = self.model.best_ask < self.model.prev_max_trade
        small_spread = self.model.best_ask - self.model.best_bid < self.spread_ratio * self.model.best_ask
        valuation = self.prices[self.quantity]
        expected_profit = valuation - self.model.best_ask > (1 - self.profit_perc) * valuation
        # self.small_spread = reasonable_offer and small_spread and expected_profit
        return reasonable_offer and small_spread and expected_profit

    def is_time_out(self):
        """
        Determines if time is almost running out, otherwise False.
        """
        # self.time_out = 1 - self.model.time / self.model.total_time < self.time_frac
        return 1 - self.model.time / self.model.total_time < self.time_frac

    def is_truthteller(self):
        """
        Determines if the agent wants to switch to truthtelling mode
        """
        remaining_steps = self.model.total_time - self.model.time
        exceeds_half = self.model.no_transactions > 0.5 * remaining_steps
        exceeds_twothird = self.model.no_transactions > 5 and self.no_transactions > 2 / 3 * remaining_steps
        
        return exceeds_half or exceeds_twothird

    def set_activity(self):
        """
        Checks if buyer can make offer thats within budget contraint and
        without losses
        """
        if self.model.best_bid != 0:
            can_shout = self.willing_to_shout()
            juicy_offer = self.is_juicy_offer()
            small_spread = self.is_small_spread()
            time_out = self.is_time_out()
            truthteller = self.is_truthteller()
            self.can_shout = can_shout
            self.juicy_offer = juicy_offer
            self.small_spread = small_spread
            self.time_out = time_out
            self.truthtelling = truthteller
            # self.active = self.can_shout and (self.juicy_offer or self.small_spread or self.time_out)
            self.active = can_shout and (juicy_offer or small_spread or time_out or truthteller)
        else:
            self.active = True

    def offer_price(self):
        """
        Generates a bid
        """
        if self.model.best_bid != 0:
            self.offer = min(self.model.best_ask, self.most)
        else:
            self.offer = self.model.min_poss_price

    def reset_offer(self):
        """
        Reset offer to initial value.
        """
        self.offer = 0
        self.most = None

    def reset_agent(self):
        """
        Resets attributes agents to initial values
        """
        super().reset_agent()
        self.most = None
        self.juicy_offer = False
        self.small_spread = False
        self.time_out = False
        self.truthtelling = False