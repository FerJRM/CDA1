#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Description of file

Name developers
"""

import os
import math
import logging
from collections import defaultdict

import pandas as pd
from scipy.stats import spearmanr
from mesa import Model
from mesa.datacollection import DataCollector
from tqdm import tqdm as pbar

import auction_ABM.auctions.cda_GS as GS
from auction_ABM.schedulers.schedules_TD import RandomTD, ImitationScheduler
from auction_ABM.agents.buyers_TD import ZI_buy, ZI_C_buy, Kaplan_buy, ZIP_buy
from auction_ABM.agents.sellers_TD import ZI_sell, ZI_C_sell, Kaplan_sell, ZIP_sell

class CDA(Model):
    """
    Continuous Double Auction model as represented in Tesauro & Das (2001).
    It manages the flow in of agents steps and collects the necessary data,
    """
    def __init__(
            self, unique_id, name, market_id, prices_buy, prices_sell, equilibrium, parameters, 
            params_strategies={"ZI_C": {}}, total_buyers_strategies={"ZI_C": 10}, 
            total_sellers_strategies={"ZI_C": 10}, save_output=False, log=True
        ):
        """
        Initialize each model with:

        unique_id: id of the model
        name: name of the auction (str)
        market_id: id of the market (int)
        prices_buy: limit prices buyers (list)
        prices_sell: limit prices sellers (list)
        equilibrium: equilibrium price, quanitity and surplus (tuple)
        parameters: paramaters such as min/max price, limit price, total periods 
                    and total time in period for auction (dict {param: value, param2, value2})
        params_strategies: agent specific parameters (nested dictionary {strategy:, {param: value}})
        total_buyers_strategies: distrbution agents on buyers' side (dict {strategy: total})
        total_sellers_strategies: distrbution agents on sellers' side (dict {strategy: total})
        save_output: boolean to indicate if data of transactions should be saved (bool)
        log: boolean to indicate if important steps in simulation should be logged (bool)
        """
        super().__init__()
        
        # initialize given attributes
        self.unique_id = unique_id
        self.name = name
        self.market_id = market_id
        self.prices_buy = prices_buy
        self.prices_sell = prices_sell
        self.eq_price = equilibrium[0]
        self.eq_quantity = equilibrium[1]
        self.eq_surplus = equilibrium[2]
        self.eq_buyer_surplus = equilibrium[3]
        self.eq_seller_surplus = equilibrium[4]
        self.activation = parameters["activation"]
        self.min_poss_price = parameters["min_price"]
        self.max_poss_price = parameters["max_price"]
        self.min_limit, self.max_limit = parameters["min_limit"], parameters["max_limit"]
        self.periods = parameters["periods"]
        self.period = 0
        self.total_time = parameters["total_time"]
        self.time = 0
        self.params_strats = params_strategies
        self.all_strategies = set(params_strategies.keys())
        self.buyers_strats = total_buyers_strategies
        self.sellers_strats = total_sellers_strategies
        self.save_output = save_output
        self.log = log

        # setup log file if required
        if log:
            log_folder = os.path.join("results", "log", name)
            os.makedirs(log_folder, exist_ok=True)
            log_auction_name = "auction_{}_ID_{}_market_{}".format(name, unique_id, market_id)
            rel_path = os.path.join(log_folder, log_auction_name)
            self.log_auction = logging.getLogger(log_auction_name)
            filehandler = logging.FileHandler(rel_path + ".log", 'w')

            self.log_auction.setLevel(logging.INFO)
            self.log_auction.addHandler(filehandler)

         # monitoring variables for during a trading period
        self.transaction_price = None
        self.outstanding_bids, self.outstanding_asks = {}, {}
        self.best_bid, self.best_bid_id = 0, None
        self.best_ask, self.best_ask_id = math.inf, None
        self.max_trade, self.prev_max_trade = 0, math.inf
        self.min_trade, self.prev_min_trade = math.inf, -math.inf
        self.agent_last_offer, self.transaction_possible = None, False
        self.surplus = defaultdict(float)
        self.quantity = defaultdict(float)
        self.efficiency = defaultdict(float)
        self.spearman_correlation = defaultdict(float)
        self.spearman_pvalue = defaultdict(float)
        self.transaction_buy = []
        self.transaction_sell = []
        self.no_transactions = 0

        # set up scheduler for auction and initialize population
        self.init_population()

         # intialize datacollector to keep track of transaction data
        self.datacollector_transactions = DataCollector(
            model_reporters={
                "ID": "unique_id",
                "Period": "period",
                "Surplus": GS.surplus_curr_period, 
                "Quantity": GS.quantity_curr_period,
                "Price": "transaction_price",
                "Squared error": GS.rmsd_transaction_price,
                "Time": "time"
            }, 
            agent_reporters={
                "ID": "model.unique_id",
                "Period": "model.period",
                "Quantity": "quantity",
                "Surplus": "surplus", 
                "Budget": "budget"
            }
        )

        # datacollector for end-of-period statistics
        self.datacollector_periods = DataCollector(
            model_reporters={
                "ID": "unique_id",
                "Period": "period",
                "Efficiency": GS.allocative_efficiency,
                "Trade ratio": GS.trade_ratio,
                "Quantity": GS.quantity_curr_period,
                "Spearman Correlation": GS.get_spearman_corr,
                "Spearman P-value": GS.get_spearman_pvalue
            },
            agent_reporters={
                "ID": "model.unique_id",
                "Period": "model.period",
                "Quantity": "quantity",
                "Surplus": "surplus",
                "Profit dispersion": "profit_dispersion",
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
            "Surplus: {}\nQuantity: {}\nMin Trade: {}\nMin Trade Prev: {}\n" \
            "Max Trade: {}\nMax Trade Prev: {}\n" \
            .format(
                self.period, self.time, self.best_bid, self.best_bid_id, 
                self.best_ask, self.best_ask_id, self.transaction_price, 
                surplus_curr_period(self), quantity_curr_period(self),
                self.min_trade, self.prev_min_trade, self.max_trade, self.prev_max_trade
            )

    def get_info_transaction(self, buyer, seller, buyer_surplus, seller_surplus):
        """
        Returns formatted string wiht some basic info about the transaction made.
        """
        return "Buyer ID: {}, Seller ID: {}, Price {}\n" \
            "Buyer surplus: {}, Seller surplus: {}, Surplus: {}, Quantity: {}\n" \
            .format(
                buyer.unique_id, seller.unique_id, self.transaction_price, buyer_surplus, 
                seller_surplus, self.surplus[self.period], self.quantity[self.period]
            )

    def init_population(self):
        """
        Initialize population of traders
        """
        self.schedule = RandomTD(self)
        self.running = True
        
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
        standard_params = (self.next_id(), self, self.prices_buy, self.eq_buyer_surplus)
        if strategy.upper() == "ZI":
            return ZI_buy(*standard_params)
        elif strategy.upper() == "ZI_C":
            return ZI_C_buy(*standard_params)
        elif strategy.upper() == "KAPLAN":
            return Kaplan_buy(*standard_params, params)
        elif strategy.upper() == "ZIP":
            return ZIP_buy(*standard_params, params)

    def create_seller(self, strategy, params=None):
        """
        Create seller depending on its strategy and limit prices
        """
        standard_params = (self.next_id(), self, self.prices_sell, self.eq_seller_surplus)
        if strategy.upper() == "ZI":
            return ZI_sell(*standard_params)
        elif strategy.upper() == "ZI_C":
            return ZI_C_sell(*standard_params)
        elif strategy.upper() == "KAPLAN":
            return Kaplan_sell(*standard_params, params)
        elif strategy.upper() == "ZIP":
            return ZIP_sell(*standard_params, params)

    def set_spearman_rank(self):
        """
        Calculates the spearman rank correlation for the current period
        """
        rank_buy = pd.Series(self.transaction_buy).rank(ascending=False)
        rank_sell = pd.Series(self.transaction_sell).rank()
        corr, p = spearmanr(rank_buy, rank_sell)
        self.spearman_correlation[self.period] = corr
        self.spearman_pvalue[self.period] = p

    def is_trade_possible(self, agent):
        """
        Determines if trade is possible (best bid and ask crosses)
        """
        if agent.market_side == "buyer":
            return agent.offer >= self.best_ask

        return agent.offer <= self.best_bid

    def update_best_price(self, agent):
        """
        Updates best bid or ask depending on the market side of agent and its
        newly offered price
        """

        self.agent_last_offer = agent

        # update log
        if self.log:
            self.log_auction.info("BEFORE UPDATE OUTSTANDING BIDS")
            self.log_auction.info(self.get_info())

        # update outstanding price
        if agent.market_side == "buyer" and agent.offer > self.best_bid:
            self.best_bid, self.best_bid_id = agent.offer, agent.unique_id
            self.outstanding_bids[agent.unique_id] = agent.offer
        elif agent.market_side == "seller" and agent.offer < self.best_ask:
            self.best_ask, self.best_ask_id = agent.offer, agent.unique_id
            self.outstanding_asks[agent.unique_id] = agent.offer

        # update log
        if self.log:
            self.log_auction.info("AFTER UPDATE OUTSTANDING BIDS")
            self.log_auction.info(self.get_info())

    def sets_best_bid(self):
        """
        Sets new best bid and the corresponding agent id
        """
        if self.outstanding_bids:
            self.best_bid_id = max(
                self.outstanding_bids, key=lambda x: self.outstanding_bids[x]
            )
            self.best_bid = self.outstanding_bids[self.best_bid_id]

        self.best_bid, self.best_bid_id = 0, None

    def sets_best_ask(self):
        """
        Sets new best ask and the corresponding agent id
        """
        if self.outstanding_asks:
            self.best_ask_id = min(
                self.outstanding_asks, key=lambda x: self.outstanding_asks[x]
            )
            self.best_ask = self.outstanding_asks[self.best_ask_id]

        self.best_ask, self.best_ask_id = math.inf, None

    def remove_outstanding_offers(self, buyer, seller):
        """
        Removes any outstanding offers from queue after the transaction
        """
        self.outstanding_bids.pop(buyer.unique_id, None)
        self.outstanding_asks.pop(seller.unique_id, None)

    def manage_order_transaction(self, buyer, seller):
        """
        Updates the agents' and model paramaters for a transaction
        """
        buyer_surplus = buyer.transaction_update(self.transaction_price)
        seller_surplus = seller.transaction_update(self.transaction_price)
        self.surplus[self.period] += buyer_surplus + seller_surplus
        self.quantity[self.period] += 1
        buyer.reset_no_transactions(), seller.reset_no_transactions()
        self.remove_outstanding_offers(buyer, seller)
        self.sets_best_bid(), self.sets_best_ask()

        # update min trading price
        if self.transaction_price < self.min_trade:
            self.min_trade = self.transaction_price

        # update max trading prices
        if self.transaction_price > self.max_trade:
            self.max_trade = self.transaction_price

        if self.log:
            self.log_auction.info(self.get_info_transaction(buyer, seller, buyer_surplus, seller_surplus))

    def make_trade(self, agent):
        """
        Make exchange between agents
        """
        if self.log:
            self.log_auction.info("TRANSACTION POSSIBLE")

        # transaction price depends on the condition if last transaction was made by a buyer
        if agent.market_side == "buyer":
            self.transaction_price = self.best_ask
            seller = self.schedule.get_agent(self.best_ask_id)
            self.transaction_buy.append(agent.get_price())
            self.transaction_sell.append(seller.get_price())
            self.manage_order_transaction(agent, seller)
            return agent.unique_id, seller.unique_id

        
        self.transaction_price = self.best_bid
        buyer = self.schedule.get_agent(self.best_bid_id)
        self.transaction_buy.append(buyer.get_price())
        self.transaction_sell.append(agent.get_price())
        self.manage_order_transaction(buyer, agent)
        
        return buyer.unique_id, agent.unique_id

    def is_end_auction(self):
        """
        Returns True if auction ended, False otherwise.
        """

        # lowest limit price of sellers still in market
        min_sell = min(
            [
                agent.get_price() for agent in self.schedule.agent_buffer() 
                if agent.market_side == "seller"
            ]
        )

        # tries to find buyer able to make trade with seller with lowers limit price
        for agent in self.schedule.agent_buffer():
            if agent.market_side == "buyer":
                price, budget = agent.get_price(), agent.get_budget()
                if price >= min_sell and budget >= min_sell:
                    return False

        # if not found auction has ended
        return True

    def reset_period(self):
        """
        Resets auction for new period to take place
        """
        self.transaction_price = None
        self.outstanding_bids, self.outstanding_asks = {}, {}
        self.best_bid, self.best_bid_id = 0, None
        self.best_ask, self.best_ask_id = math.inf, None
        self.prev_min_trade, self.prev_max_trade = self.min_trade, self.max_trade
        self.min_trade, self.max_trade = math.inf, 0
        self.transaction_buy, self.transaction_sell = [], []
        self.agent_last_offer, self.transaction_possible = None, False
        self.no_transactions = 0
        
        self.schedule.reset_agents()

    def step(self):
        """
        Run auction.
        """

        # run auction for given amount of periods, each having the same total time
        descr = "period bar auction {} with ID {} and market {}".format(self.name, self.unique_id, self.market_id)
        for self.period in pbar(range(self.periods), desc=descr):
            for self.time in range(self.total_time):
                
                # update log
                if self.log:
                    self.log_auction.info("BEORE STEP IN AUCTION")
                    self.log_auction.info(self.get_info())

                # update data if transaction is made during step
                if self.schedule.step():
                    self.no_transactions = 0
                else:
                    self.no_transactions += 1
                
                # update log
                if self.log:
                    self.log_auction.info("AFTER STEP IN AUCTION")
                    self.log_auction.info(self.get_info())

                # determines if all possible trades are already done, if so terminate period
                if self.is_end_auction():
                    break

            # reset auction for next period
            self.schedule.set_profit_dispersion()
            self.set_spearman_rank()
            self.efficiency[self.period] = GS.allocative_efficiency(self)
            self.datacollector_transactions.collect(self)
            self.datacollector_periods.collect(self)
            self.reset_period()

            # update log with final results period
            if self.log:
                self.log_auction.info("Auction period {} ended in time step {}".format(self.period, self.time))
                self.log_auction.info(
                    "Efficiency {}, Surplus: {}, Quantity traded {}".format(
                        self.surplus[self.period] / self.eq_surplus, 
                        self.surplus[self.period], 
                        self.quantity[self.period]
                    )
                )

        self.running = False

        # update datacollectors with end of period information
        data_transactions = self.datacollector_transactions.get_model_vars_dataframe()
        data_periods = self.datacollector_periods.get_model_vars_dataframe()
        data_agents = self.datacollector_transactions.get_agent_vars_dataframe()
        data_periods_agents = self.datacollector_periods.get_agent_vars_dataframe()

        return data_transactions, data_periods, data_agents, data_periods_agents

class ReplicationByImitation(CDA):
    def __init__(
            self, unique_id, name, market_id, prices_buy, prices_sell, equilibrium, parameters, 
            params_strategies={"ZI_C": {}}, total_buyers_strategies={"ZI_C": 10}, 
            total_sellers_strategies={"ZI_C": 10}, save_output=False, log=True
    ):
    
        super().__init__(
            unique_id, name, market_id, prices_buy, prices_sell, equilibrium, parameters, 
            params_strategies, total_buyers_strategies, 
            total_sellers_strategies, save_output, log
        )

        # additional attributes for evolutionary development
        self.evo_process = []
        self.periods_no_switches = 0

        # different datacollector for end-of-period data (for evolutionary process)
        self.datacollector_periods = DataCollector(
            model_reporters={
                "ID": "unique_id",
                "Period": "period",
                "Efficiency": GS.allocative_efficiency,
                "Trade ratio": GS.trade_ratio,
                "Quantity": GS.quantity_curr_period,
                "Spearman Correlation": GS.get_spearman_corr,
                "Spearman P-value": GS.get_spearman_pvalue
            },
            agent_reporters={
                "Strategy": "strategy",
                "ID": "model.unique_id",
                "Period": "model.period",
                "Quantity": "quantity",
                "Surplus": "surplus",
                "Profit dispersion": "profit_dispersion",
                "Budget": "budget"
            }
        )

    def init_population(self):
        """
        Initialize population of traders
        """
        self.schedule = ImitationScheduler(self)
        self.running = True
        
        for strategy, buyers in self.buyers_strats.items():
            for _ in range(buyers):
                agent = self.create_buyer(strategy, self.params_strats[strategy])
                self.schedule.add(agent)

        for strategy, sellers in self.sellers_strats.items():
            for _ in range(sellers):
                agent = self.create_seller(strategy, self.params_strats[strategy])
                self.schedule.add(agent)

    def update_number_strategies(self):
        """
        Determines the amount of traders per strategy for current period
        """
        info = {"ID":  self.unique_id, "Period": self.period}
        for agent in self.schedule.agent_buffer():
            if agent.strategy in info:
                info[agent.strategy] += 1
            else:
                info[agent.strategy] = 1

        self.evo_process.append(info)

    def pop_has_converged(self):
        """
        Determines if the popolution has converged towards an equilibrium of
        strategies (not necesarily a Nash equilibrium)
        """
        return self.periods_no_switches > 15

    def step(self):
        """
        Run auction.
        """

        # run auction for given amount of periods, each having the same total time
        descr = "period bar auction {} with ID {} and market {}".format(self.name, self.unique_id, self.market_id)
        for self.period in pbar(range(self.periods), desc=descr):
            for self.time in range(self.total_time):
                
                # update log
                if self.log:
                    self.log_auction.info("BEORE STEP IN AUCTION")
                    self.log_auction.info(self.get_info())

                # update data if transaction is made during step
                if self.schedule.step():
                    self.no_transactions = 0
                else:
                    self.no_transactions += 1
                
                # update log
                if self.log:
                    self.log_auction.info("AFTER STEP IN AUCTION")
                    self.log_auction.info(self.get_info())

                # determines if all possible trades are already done, if so terminate period
                if self.is_end_auction():
                    break

            # reset auction for next period
            self.schedule.set_profit_dispersion()
            self.set_spearman_rank()
            self.efficiency[self.period] = GS.allocative_efficiency(self)
            self.datacollector_transactions.collect(self)
            self.datacollector_periods.collect(self)
            self.update_number_strategies()
            self.reset_period()

            # update log with final results period
            if self.log:
                self.log_auction.info("Auction period {} ended in time step {}".format(self.period, self.time))
                self.log_auction.info(
                    "Efficiency {}, Surplus: {}, Quantity traded {}".format(
                        self.surplus[self.period] / self.eq_surplus, 
                        self.surplus[self.period], 
                        self.quantity[self.period]
                    )
                )

            # end run if population has converged
            if self.pop_has_converged():
                print("\nhas converged")
                break

        self.running = False

        # update datacollectors with end of period information
        data_transactions = self.datacollector_transactions.get_model_vars_dataframe()
        data_periods = self.datacollector_periods.get_model_vars_dataframe()
        data_agents = self.datacollector_transactions.get_agent_vars_dataframe()
        data_periods_agents = self.datacollector_periods.get_agent_vars_dataframe()
        data_evo = pd.DataFrame(self.evo_process)

        return data_transactions, data_periods, data_agents, data_periods_agents, data_evo