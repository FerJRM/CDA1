#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Description of file

Name developers
"""

import math
import random

from mesa import Agent

class ZI_sell(Agent):
    market_side = "seller"
    strategy = "ZI"

    def __init__(self, unique_id, model, valuation, eq_surplus, commodities):
        super().__init__(unique_id, model)
        # self.prices = prices
        # self.tot_commodities = len(prices)
        self.valuation = valuation
        self.tot_commodities = commodities
        self.quantity = 0
        self.prev_quantity = 0
        self.budget = 0
        self.eq_surplus = eq_surplus
        self.surplus = 0
        self.prev_surplus = 0
        self.profit_dispersion = 0
        self.offer = math.inf
        self.in_market = True
        self.active = True
        self.no_transactions = 0

    def get_info(self):
        """
        Returns a formatted string containing the current state of agent
        """
        return f"==============================================" \
            f"\nID: {self.unique_id} " \
            f"\nAgent: {self.strategy} " \
            f"\nSide: {self.market_side} " \
            f"\nValuation: {self.valuation} " \
            f"\nOffer: {self.offer} " \
            f"\nQuantity: {self.quantity} " \
            f"\nBudget: {self.budget}" \
            f"\n================================================="

    def return_import_params(self):
        """
        Returns important parameters for imitation process
        """
        return self.quantity, self.surplus

    def set_import_params(self, values):
        """
        Sets the values for the important params
        """
        self.quantity, self.surplus = values

    def still_commodities(self):
        """
        Returns True if agent still has commodites left, otherwise False
        """
        # return self.quantity < len(self.prices)
        return self.tot_commodities > self.quantity

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

    def willing_to_shout(self):
        """
        Determines if the seller is willing to shout
        """
        return True

    def set_activity(self):
        """
        Determines if buyer is active (can shout price)
        """
        self.active = self.willing_to_shout()

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
            # return self.prices[self.quantity]
            return self.valuation
        
        return math.inf

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
        if self.model.best_ask == math.inf:
            # self.offer = random.randint(self.model.min_poss_price, self.model.max_poss_price)
            self.offer = random.uniform(self.model.min_poss_price, self.model.max_poss_price)
        else:
            # self.offer = random.randint(self.model.min_poss_price, self.model.best_ask - 1)
            self.offer = random.uniform(self.model.min_poss_price, self.model.best_ask - 0.01)

        return self.offer

    def transaction_update(self, price):
        """
        Update surplus, quantity bought, budget and price index for a certain
        transaction price
        """
        # surplus = price - self.prices[self.quantity]
        surplus = price - self.valuation
        self.surplus += surplus
        self.budget += price
        self.quantity += 1

        return surplus

    def update_params(self):
        """
        Update the parameters of the agent after a time step in 
        a double auction
        """
        pass

    def reset_offer(self):
        """
        Reset offer to initial value.
        """
        self.offer = math.inf

    def reset_agent(self):
        """
        Resets attributes agents to initial values
        """
        self.prev_quantity = self.quantity
        self.quantity = 0
        self.budget = 0
        self.offer = math.inf
        self.prev_surplus = self.surplus
        self.surplus = 0
        self.in_market = True
        self.active = True
        self.no_transactions = 0

    def step(self):
        """
        Perform one action (step) in the auction for the agent
        """
        return self.offer_price()

class ZI_C_sell(ZI_sell):
    """
    An Zero Intelligence Constrained agent as described by Gode & Sunder (1993).
    Note, it acts as a seller in a double auction
    """
    market_side = "seller"
    strategy = "ZI_C"

    def willing_to_shout(self):
        """
        Determines if the seller is willing to shout
        """
        # return self.prices[self.quantity] < self.model.best_ask
        return self.valuation < self.model.best_ask

    def set_activity(self):
        if self.still_commodities():
            self.active = self.willing_to_shout()
        else:
            self.active = False

    def offer_price(self):
        # valuation = self.prices[self.quantity]
        if self.model.best_ask == math.inf:
            # self.offer = random.randint(valuation, self.model.max_poss_price)
            self.offer = random.uniform(self.valuation, self.model.max_poss_price)
        else:
            # self.offer = random.randint(valuation, self.model.best_ask - 1)
            self.offer = random.uniform(self.valuation, self.model.best_ask - 0.01)

        return self.offer

class ZIP_sell(ZI_C_sell):
    """
    ZIP trader for double auction as described by Cliff D. & Bruten J. (1997)
    """
    market_side = "seller"
    strategy = "ZIP"

    def __init__(self, unique_id, model, valuation, eq_surplus, commodities, params):
        super().__init__(unique_id, model, valuation, eq_surplus, commodities)
        self.profit_margin = random.uniform(*params["profit_margin_sellers"])
        # self.profit_margins = [random.uniform(*params["profit_margin_sellers"]) for _ in range(self.tot_commodities)]
        self.learning_rate = random.uniform(*params["learning_rate"])
        self.momentum_coeff = random.uniform(*params["momentum_coeff"])
        self.momentum = 0
        # self.momentum = [0] * self.tot_commodities
        self.decreasing_rel_target = params["decreasing_rel_target"]
        self.increasing_rel_target = params["increasing_rel_target"]
        self.decreasing_abs_target = params["decreasing_abs_target"]
        self.increasing_abs_target = params["increasing_abs_target"]

    def get_info(self):
        """
        Returns a formatted string containing the current state of agent
        """
        return f"==============================================" \
            f"\nID: {self.unique_id} " \
            f"\nAgent: {self.strategy} " \
            f"\nSide: {self.market_side} " \
            f"\nValuation: {self.valuation} " \
            f"\nOffer: {self.offer} " \
            f"\nQuantity: {self.quantity} " \
            f"\nBudget: {self.budget}" \
            f"\nProfit margin: {self.profit_margin}" \
            f"\nLearning rate: {self.learning_rate}" \
            f"\nMomentum coeffiecient: {self.momentum_coeff}" \
            f"\nMomentum: {self.momentum}" \
            f"\n================================================="

    def return_import_params(self):
        """
        Returns important parameters for imitation process
        """
        values = (
            self.quantity, self.surplus, self.profit_margin, 
            self.learning_rate, self.momentum_coeff, 
            self.decreasing_rel_target, self.increasing_rel_target,
            self.decreasing_abs_target, self.increasing_abs_target
        )
        return values

    def set_import_params(self, values):
        """
        Sets import parameter values during imitation process
        """
        self.quantity, self.surplus = values[0], values[1]
        self.profit_margin, self.learning_rate, self.momentum_coeff = values[2], values[3], values[4]
        self.decreasing_rel_target, self.increasing_rel_target = values[5], values[6]
        self.decreasing_abs_target, self.increasing_abs_target = values[7], values[8]

    def willing_to_shout(self):
        """
        Determines if an agent is willing to shout
        """
        # is_endowed = self.prices[self.quantity] < self.model.best_ask
        is_endowed = self.valuation < self.model.best_ask
        # offer = self.prices[self.quantity] * (1 + self.profit_margins[self.quantity % self.tot_commodities])
        # offer = self.prices[self.quantity] * (1  + self.profit_margin)
        offer = self.valuation *  (1 + self.profit_margin)
        is_better_ask = offer < self.model.best_ask
        return is_endowed and is_better_ask

    def offer_price(self):
        """
        Generates an ask
        """
        self.offer = self.valuation * (1 + self.profit_margin)
        # self.offer = self.prices[self.quantity] * (1 + self.profit_margin)
        # self.offer = self.prices[self.quantity] * (1 + self.profit_margins[self.quantity % self.tot_commodities])
        return self.offer

    def margin_within_bounds(self):
        """
        Ensures that profit margin is within bounds
        """
        # if self.profit_margins[self.quantity % self.tot_commodities] < 0:
        #     self.profit_margins[self.quantity % self.tot_commodities] = 0
        if self.profit_margin < 0:
            self.profit_margin = 0

    # def margin_within_bounds(self, quantity):
    #     """
    #     Ensures that profit margin is within bounds
    #     """
    #     if self.profit_margins[quantity] < 0:
    #         self.profit_margins[quantity] = 0
    #     # if self.profit_margin < 0:
    #     #     self.profit_margin = 0

    def determine_target_price(self, move, last_shout):
        """
        """
        if move == "increase":
            r = random.uniform(*self.increasing_rel_target)
            a = random.uniform(*self.increasing_abs_target)
            return r * last_shout + a

        r = random.uniform(*self.decreasing_rel_target)
        a = random.uniform(*self.decreasing_abs_target)
        return  r * last_shout + a

    def widrow_holf_delta(self, target_price, offer):
        return self.learning_rate * (target_price - offer)

    def determine_momentum(self, target_price, offer):
        if self.model.time == 0:
            return self.momentum

        x = self.momentum_coeff * self.momentum
        y = (1 - self.momentum_coeff) * self.widrow_holf_delta(target_price, offer)
        self.momentum = x + y

        # NIET NODIG, ALLEEN TIJDENS t=0 ZOALS BOVEN NODIG
        # if self.momentum < 0:
        #     self.momentum = 0
        # elif self.momentum > 1:
        #     self.momentum = 1

        return self.momentum

    # def determine_momentum(self, quantity, target_price, offer):
    #     if self.model.time == 0:
    #         return

    #     x = self.momentum_coeff * self.momentum[quantity]
    #     y = (1 - self.momentum_coeff) * self.widrow_holf_delta(target_price, offer)
    #     self.momentum[quantity] = x + y

    #     if self.momentum[quantity] < 0:
    #         self.momentum[quantity] = 0
    #     elif self.momentum[quantity] > 1:
    #         self.momentum[quantity] = 1

    def adjust_profit_margin(self, move, offer, last_shout):
        target_price = self.determine_target_price(move, last_shout)
        momentum = self.determine_momentum(target_price, offer)
        # if transaction_made:
        #     valuation = self.prices[self.quantity - 1]
        # else:
        #     valuation = self.prices[self.quantity]
        # self.profit_margins[self.quantity % self.tot_commodities] = (offer + momentum) / valuation - 1
        self.profit_margin = (offer + momentum) / self.valuation - 1
        self.margin_within_bounds()

    # def adjust_profit_margin(self, move, quantity, offer, last_shout):
    #     target_price = self.determine_target_price(move, last_shout)
    #     # self.determine_momentum(quantity, target_price, offer)
    #     valuation = self.prices[quantity]
    #     self.profit_margins[quantity] = (offer + momentum) / valuation - 1
    #     self.margin_within_bounds(quantity)

    #     # valuation = self.prices[self.quantity]
    #     # self.profit_margins[self.quantity % self.tot_commodities] = (offer + momentum) / valuation - 1
    #     # self.profit_margin = (offer + momentum) / valuation - 1
    #     # self.margin_within_bounds()

    def update_params(self):
        """
        Update the parameters of the agent after a time step in 
        a double auction
        """

        offer = self.offer_price()
        side_last_offer = self.model.agent_last_offer.market_side.lower()

        # for quantity in range(self.tot_commodities):
        # offer = self.prices[quantity] * (1 + self.profit_margins[quantity])

        if self.model.transaction_possible:

            # raise profit margin 
            if offer <= self.model.transaction_price:
                self.adjust_profit_margin("increase", offer, self.model.transaction_price)
                # self.adjust_profit_margin("increase", quantity, offer, self.model.transaction_price)

            # lower profit margin
            elif side_last_offer == "buyer" and offer >= self.model.transaction_price and self.in_market:
                self.adjust_profit_margin("decrease", offer, self.model.transaction_price)
                # self.adjust_profit_margin("decrease", quantity, offer, self.model.transaction_price)

        else:

            # lower profit margin
            if side_last_offer == "seller" and offer >= self.model.agent_last_offer.offer and self.in_market:
                self.adjust_profit_margin("decrease", offer, self.model.agent_last_offer.offer)
                # self.adjust_profit_margin("decrease", quantity, offer, self.model.agent_last_offer.offer)

    def reset_agent(self):
        """
        Resets attributes agents to initial values
        """
        super().reset_agent()
        self.momentum = 0
        # self.momentum = [0] * self.tot_commodities

class Kaplan_sell(ZI_sell):
    """
    Implementation of an Kaplan agent (Rust, Palm & Miller, 1993)
    """
    market_side = "seller"
    strategy = "KAPLAN"

    def __init__(self, unique_id, model, valuation, eq_surplus, commodities, params):
        super().__init__(unique_id, model, valuation, eq_surplus, commodities)
        self.spread_ratio = params["spread_ratio"]
        self.profit_perc = params["profit_perc"]
        self.time_frac = params["time_frac"]
        self.most = None

    def get_info(self):
        """
        Returns a formatted string containing the current state of agent
        """
        return f"==============================================" \
            f"\nID: {self.unique_id} " \
            f"\nAgent: {self.strategy} " \
            f"\nSide: {self.market_side} " \
            f"\nValuation: {self.valuation} " \
            f"\nQuantity: {self.quantity} " \
            f"\nBudget: {self.budget}" \
            f"\nOffer: {self.offer} " \
            f"\nTime fraction: {self.time_frac}" \
            f"\nSpread ratio: {self.spread_ratio}" \
            f"\nProfit percentage: {self.profit_perc}" \
            f"\nCan shout: {self.willing_to_shout()}" \
            f"\nJuicy offer: {self.is_juicy_offer()}" \
            f"\nSmall spread: {self.is_small_spread()}" \
            f"\nTime out: {self.is_time_out()}" \
            f"\nTruthtelling mode: {self.is_truthteller()}" \
            f"\nMost: {self.most}" \
            f"\n================================================="

    def return_import_params(self):
        """
        Returns important params for imitation process
        """
        return self.quantity, self.surplus, self.spread_ratio, self.profit_perc, self.time_frac

    def set_import_params(self, values):
        """
        Set important params during imitation process
        """
        self.quantity, self.surplus, self.spread_ratio, self.profit_perc, self.time_frac = values

    def willing_to_shout(self):
        """
        Determines if the seller is willing to shout
        """
        best_bid = self.model.best_bid
        # if self.quantity != len(self.prices) - 1:
        #     next_token = self.prices[self.quantity + 1]
        # else:
        #     next_token = self.prices[self.quantity]

        if best_bid != 0:
            # self.most = max(best_bid, next_token + 1)
            self.most = max(best_bid, self.valuation + 1)
        else:
            # self.most = next_token + 1
            self.most = self.valuation + 1

        is_better_ask = self.most < self.model.best_ask
        # is_endowed =  self.prices[self.quantity] <= self.most

        return is_better_ask

    def is_juicy_offer(self):
        """
        Determines if the best ask is less than the minimum trade price trade 
        price in the previous period.
        """
        return self.model.best_bid > self.model.prev_max_trade

    def is_small_spread(self):
        """
        Determines if reasonalbe offer has been made, bid-ask spread is small enough
        and the expected profit is sufficient.
        """
        reasonable_offer = self.model.best_bid > self.model.prev_min_trade
        small_spread = self.model.best_ask - self.model.best_bid < self.spread_ratio * self.model.best_bid
        # valuation  = self.prices[self.quantity]
        expected_profit = self.model.best_bid - self.valuation > (1 + self.profit_perc) * self.valuation

        return reasonable_offer and small_spread and expected_profit

    def is_time_out(self):
        """
        Determines if time is almost running out, otherwise False.
        """
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
        Checks if seller can make offer thats within budget contraint and
        without losses
        """
        if self.model.best_ask != math.inf:
            can_shout = self.willing_to_shout()
            juicy_offer = self.is_juicy_offer()
            small_spread = self.is_small_spread()
            time_out = self.is_time_out()
            truthteller = self.is_truthteller()
            self.active = can_shout and (juicy_offer or small_spread or time_out or truthteller)
        else:
            self.active = True

    def offer_price(self):
        """
        Generates a ask
        """
        if self.model.best_ask != math.inf:
            self.offer = max(self.model.best_bid, self.most)
        else:
            self.offer = self.model.max_poss_price

        return self.offer

    def reset_offer(self):
        """
        Reset offer to initial value.
        """
        self.offer = math.inf
        self.most = None

    def reset_agent(self):
        """
        Resets attributes agents to initial values
        """
        super().reset_agent()
        self.most = None
