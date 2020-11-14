#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Description of file

Name developers
"""

import math
from collections import defaultdict

from mesa import Model
from mesa.datacollection import DataCollector
from tqdm import tqdm as pbar

from classes.schedulers.schedules import RandomGS
from classes.agents.zero_intelligence import ZI_buy, ZI_sell

class CDA(Model):
    """
    Continuous Double Auction model as represented in Gode en Sunder (1993).
    It manages the flow in of agents steps and collects the necessary data,
    """
    def __init__(
            self, sim, prices_buy, prices_sell, equilibrium, parameters, 
            params_strategies={"ZI": {}}, total_buyers_strategies={"ZI": 10}, 
            total_sellers_strategies={"ZI": 10}, save_output=False
        ):
        super().__init__(self)
        
        self.sim = sim
        self.prices_buy = prices_buy
        self.prices_sell = prices_sell
        self.eq_price, self.eq_quantity, self.eq_surplus = equilibrium
        self.min_poss_price = parameters["min_price"]
        self.max_poss_price = parameters["max_price"]
        self.min_limit, self.max_limit = parameters["min_limit"], parameters["max_limit"]
        self.periods = parameters["periods"]
        self.period = 0
        self.total_time = parameters["total_time"]
        self.time = 0
        self.params_strats = params_strategies
        self.buyers_strats = total_buyers_strategies
        self.sellers_strats = total_sellers_strategies
        self.save_output = save_output

        # monitoring variables for during a trading period
        self.transaction_price = None
        self.best_bid, self.best_bid_id = 0, None
        self.best_ask, self.best_ask_id = math.inf, None
        self.surplus = defaultdict(float)
        self.quantity = defaultdict(float)

        # set up scheduler for auction
        self.schedule = RandomGS(self)
        self.running = True

        # intialize population and datacollector
        self.init_population()
        self.datacollector = DataCollector(
            model_reporters={
                "Simulation": "sim",
                "Period": "period",
                "Surplus": CDA.surplus_curr_period, 
                "Quantity": CDA.quantity_curr_period,
                "Price": CDA.last_transaction_price,
                "Time": CDA.get_time
            }, 
            agent_reporters={
                "Quantity": "quantity",
                "Surplus": "surplus", 
                "Budget": "budget"
            }
        )

    def get_info(self):
        """
        Returns a string with basic information about the current state of the
        auction.
        """
        return "Period: {}\nTime: {}\nBest Bid: {}\nBid ID: {}\n" \
            "Best Ask: {}\nAsk ID: {}\nLast Price: {}\n" \
            .format(
                self.period, self.time, self.best_bid, self.best_bid_id, 
                self.best_ask, self.best_ask_id, self.transaction_price
            )

    def init_population(self):
        """
        Initialize population of traders
        """
        
        for strategy, buyers in self.buyers_strats.items():
            for _ in range(buyers):
                agent = self.create_buyer(strategy, self.params_strats[strategy])
                self.schedule.add(agent)

        for strategy, sellers in self.sellers_strats.items():
            for _ in range(sellers):
                agent = self.create_seller(strategy, self.params_strats[strategy])
                self.schedule.add(agent)

    def create_buyer(self, strategy, params=None):
        """
        Create buyer depending on its strategy, limit prices
        """

        if strategy.upper() == "ZI":
            return ZI_buy(self.next_id(), self, self.prices_buy)
        # elif strategy.upper(0 == "KAPLAN"):
        #     return K

    def create_seller(self, strategy, params=None):
        """
        Create seller depending on its strategy and limit prices
        """
        if strategy.upper() == "ZI":
            return ZI_sell(self.next_id(), self, self.prices_sell)

    def surplus_curr_period(self):
        """
        Returns surplus of current period
        """
        return self.surplus[self.period]

    def quantity_curr_period(self):
        """
        Returns quantity traded in current period
        """
        return self.quantity[self.period]

    def last_transaction_price(self):
        """
        Returns the latest known transaction price
        """
        return self.transaction_price

    def get_time(self):
        """
        Returns current time stamp
        """
        return self.time

    def reset_bids(self):
        """
        Resets outstanding bid and id
        """
        self.best_bid, self.best_bid_id = 0, None

    def reset_asks(self):
        """
        Resets outstanding ask and id
        """
        self.best_ask, self.best_ask_id = math.inf, None

    def is_trade_possible(self, agent):
        """
        Determines if trade is possible (best bid and ask crosses)
        """
        if agent.market_side == "buyer":
            return agent.offer >= self.best_ask

        return agent.offer <= self.best_bid

    def make_trade(self, agent):
        """
        Make exchange between agents
        """
        if agent.market_side == "buyer":
            self.transaction_price = self.best_ask
            seller = self.schedule.get_agent(self.best_ask_id)
            buyer_surplus = agent.transaction_update(self.transaction_price)
            seller_surplus = seller.transaction_update(self.transaction_price)
            self.surplus[self.period] += buyer_surplus + seller_surplus
            self.quantity[self.period] += 1

        else:
            self.transaction_price = self.best_bid
            buyer = self.schedule.get_agent(self.best_bid_id)
            buyer_surplus = buyer.transaction_update(self.transaction_price)
            seller_surplus = agent.transaction_update(self.transaction_price)
            self.surplus[self.period] += buyer_surplus + seller_surplus
            self.quantity[self.period] += 1

        # reset outstanding bid and ask
        self.reset_bids(), self.reset_asks()

    def update_best_price(self, agent):
        """
        Updates best bid or ask depending on the market side of agent and its
        newly offered price
        """
        if agent.market_side == "buyer":
            self.best_bid, self.best_bid_id = agent.offer, agent.unique_id
        else:
            self.best_ask, self.best_ask_id = agent.offer, agent.unique_id

    def is_end_auction(self):
        """
        Returns True if auction ended, False otherwise.
        """
        min_sell = min([agent.get_price() for agent in self.schedule.agent_buffer() if agent.market_side == "seller"])

        for agent in self.schedule.agent_buffer():
            if agent.market_side == "buyer":
                price, budget = agent.get_price(), agent.get_budget()
                if price >= min_sell and budget >= min_sell:
                    return False

        return True

    def reset_period(self):
        """
        Resets auction for new period to take place
        """
        self.transaction_price = None
        self.best_bid, self.best_bid_id = 0, None
        self.best_ask, self.best_ask_id = math.inf, None
        
        self.schedule.reset_agents()

    def step(self):
        """
        """
        return self.schedule.step()

    def run_model(self):
        """
        """
        for self.period in range(self.periods):
            for self.time in range(self.total_time):
                # print(self.get_info())
                transaction_made = self.step()
                if transaction_made:
                    self.datacollector.collect(self)
                # print(self.get_info())

                if self.is_end_auction():
                    self.reset_period()
                    break

            print("Auction period {} ended in time step {}".format(self.period, self.time))
            print(
                "Efficiency {} Quantity traded {}".format(
                    self.surplus[self.period] / self.eq_surplus, self.quantity[self.period]
                )
            )