#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Description of file

Name developers
"""

import random

from mesa.time import BaseScheduler

from auction_ABM.agents.buyers import ZI_C_buy, Kaplan_buy, ZIP_buy
from auction_ABM.agents.sellers import ZI_C_sell, Kaplan_sell, ZIP_sell

class RandomGS(BaseScheduler):
    """
    Random scheduler for the simulations based on Gode and Sunder their research.
    """

    def get_agent(self, unique_id):
        """
        Returns the agent for the given id
        """
        return self._agents[unique_id]

    def get_offers_agents(self):
        """
        Let all the active shout a bid or ask and returns the made bids and asks
        """
        bids, asks = {}, {}
        for agent in self.agent_buffer():
            agent.set_activity(), agent.set_in_market()
            if agents.is_active() and agent.is_in_market():
                if agent.market_side.lower() == "buyer":
                    bids[agent.unique_id] = agent.step()
                else:
                    asks[agent.unique_id] = agent.step()

        return bids, asks

    def get_active_agent(self):
        """
        Collect all active agents and randomly chooses one that will offer a price
        """

        # collect active agents
        active_agents = []
        for agent in self.agent_buffer():
            agent.set_activity(), agent.set_in_market()
            if agent.is_active() and agent.is_in_market():
                active_agents.append(agent)
        
        # randomly choose active agent
        if active_agents:
            return self.model.random.choice(active_agents)

        # none found
        return None

    def reset_offers_agents(self):
        """
        Reset offers agents to intial value.
        """
        for agent in self.agent_buffer():
            agent.reset_offer()

    def update_no_transactions(self, buyer_id=-1, seller_id=-1):
        """
        Update the number of steps in which no transaction occur for each
        agent in double auction except those that made a transaction
        """
        for agent in self.agent_buffer():
            if agent.unique_id != buyer_id and agent.unique_id != seller_id:
                agent.update_no_transactions()
            else:
                agent.reset_no_transactions()

    def set_profit_dispersion(self):
        """
        Set profit dispersion of each agent
        """
        for agent in self.agent_buffer():
            agent.set_profit_dispersion()

    def reset_agents(self):
        """
        Resets all agents' attributes to their intial values and reset
        time and step attributes scheduler
        """
        for agent in self.agent_buffer():
            agent.reset_agent()

        self.time = 0
        self.steps = 0

    def update_params_agents(self):
        """
        Update paramater of agents at the and of a time step
        """
        for agent in self.agent_buffer():
            agent.update_params()

    def step(self):
        """
        Executes the steps of all agents, one at a time, in random order. 
        Note that it is possible that none of the agents is selected. If so, 
        no action takes place.

        The function returns True if a transaction has been made, otherwise False
        """

        # only perform step if actie agent is selected
        agent, self.model.transaction_possible = self.get_active_agent(), False
        if agent is not None:

            self.model.agent_last_offer = agent
            
            # update log
            if self.model.log:
                self.model.log_auction.info("BEFORE STEP AGENT")
                self.model.log_auction.info(agent.get_info())

            # perform agent's step
            _ = agent.step()

            # update log
            if self.model.log:
                self.model.log_auction.info("AFTER STEP AGENT")
                self.model.log_auction.info(agent.get_info())

            # determines if trade needs to be made or outstanding bid/ask 
            # should be updated
            if self.model.is_trade_possible(agent):
                self.model.transaction_possible = True
                self.model.update_best_price(agent)
                _ = self.model.make_trade(agent)
            else:
                self.model.update_best_price(agent)

        if self.model.log:
            self.model.log_auction.info("BEFORE UPDATING PARAMETERS")
            for agent in self.agent_buffer():
                self.model.log_auction.info(agent.get_info())

        # update parameters agents
        self.update_params_agents()

        if self.model.log:
            self.model.log_auction.info("AFTER UPDATING PARAMETERS")
            for agent in self.agent_buffer():
                self.model.log_auction.info(agent.get_info())

        # update time and steps of auction
        self.steps += 1
        self.time += 1

        return self.model.transaction_possible

class EvoRandomGS(RandomGS):
    """
    Scheduler for an evolutionary CDA tournament. The evolutionary process is 
    done by means of "replication by imitation".
    """

    def replace_buyer(self, agent, new_strategy, surplus, quantity):
        """
        Replace a buyer by its new strategy, keep track of its surplus and 
        quantity and reset its parameters. Returns the newly made agent
        """

        # make new agent
        standard_params = [agent.unique_id, self.model, self.model.prices_buy, self.model.eq_buyer_surplus]
        if new_strategy.upper() == "ZI_C":
            new_agent = ZI_C_buy(*standard_params)
        elif new_strategy.upper() == "KAPLAN":
            new_agent = Kaplan_buy(*standard_params, self.model.params_strats[new_strategy.upper()])
        elif new_strategy.upper() == "ZIP":
            new_agent = ZIP_buy(*standard_params, self.model.params_strats[new_strategy.upper()])

        # keep track of surplus and quantity; reset agent for next period
        new_agent.surplus = surplus
        new_agent.quantity = quantity
        new_agent.reset_agent()

        return new_agent

    def replace_seller(self, agent, new_strategy, surplus, quantity):
        """
        Replace a seller by its new strategy, keep track of its surplus and 
        quantity and reset its parameters. Returns the newly made agent
        """

        # make new agent
        standard_params = [agent.unique_id, self.model, self.model.prices_sell, self.model.eq_seller_surplus]
        if new_strategy.upper() == "ZI_C":
            new_agent = ZI_C_sell(*standard_params)
        elif new_strategy.upper() == "KAPLAN":
            new_agent = Kaplan_sell(*standard_params, self.model.params_strats[new_strategy.upper()])
        elif new_strategy.upper() == "ZIP":
            new_agent = ZIP_sell(*standard_params, self.model.params_strats[new_strategy.upper()])

        # keep track of surplus and quantity; reset agent for next period
        new_agent.surplus = surplus
        new_agent.quantity = quantity
        new_agent.reset_agent()

        return new_agent

    def determine_new_strategy(self, agent, other, switches):
        """
        Determines if the agent decides to switch strategies or not by comparing
        its own performance to a randomly selected other trader of the same
        market side
        """

        # own profit is better, keep strategy
        if agent.surplus > other.surplus:
            strategy = agent.strategy

        # profit other is better, switch strategy depending on relative difference
        elif agent.surplus < other.surplus:
            prob = (other.surplus - agent.surplus) / other.surplus      
            if random.random() < prob:
                strategy = other.strategy
                if strategy != agent.strategy:
                    switches += 1
            else:
                strategy = agent.strategy

        # surplus is equal so choice depends on the quantity of both agents
        elif agent.quantity > other.quantity:
            strategy = agent.strategy
        elif agent.quantity < other.quantity:
            strategy = other.strategy
            if strategy != agent.strategy:
                switches += 1

        # quantity is also equal, so randomly choose new strategy
        elif random.random() < 0.5:
            strategy = agent.strategy
        else:
            strategy = other.strategy
            if strategy != agent.strategy:
                switches += 1

        # return new strategy and the updated total switches
        return strategy, switches

    def replace_agents(self, new_strategies, surplus_agents, quantity_agents):
        """
        Replace all agents by their new strategies
        """
        # replace each agent by its new strategy
        for agent in self.agent_buffer():
            if agent.market_side.lower() == "buyer":
                new_agent = self.replace_buyer(
                    agent, new_strategies[agent.unique_id], 
                    surplus_agents[agent.unique_id], quantity_agents[agent.unique_id]
                )
            else:
                new_agent = self.replace_seller(
                    agent, new_strategies[agent.unique_id],
                    surplus_agents[agent.unique_id], quantity_agents[agent.unique_id]
                )
            
            self._agents[agent.unique_id] = new_agent

    def reset_agents(self):
        """
        Determines the new strategy of all agents by means of "replication by 
        imitation": each agent compares its performance to a randomly selected 
        agent (including copies) and chooses to keep its own strategy or to switch
        to the strategy of the other (imitation)
        """

        switches = 0

        # start finding the new strategies of all agents, also keep track of 
        # their surplus and quantity
        new_strategies = {}
        surplus_agents = {}
        quantity_agents = {}
        for agent in self.agent_buffer():

            # if current profit is better than last period then keep strategy
            if agent.surplus >= agent.prev_surplus:
                new_strategies[agent.unique_id] = agent.strategy
                surplus_agents[agent.unique_id] = agent.surplus
                quantity_agents[agent.unique_id] = agent.quantity
                continue

            # randomly select other agent from same market side
            while True:
                other = self.model.random.choice(self.agents)
                if agent.market_side.upper() == other.market_side.upper():
                    break

            # determines which strategy to choose by means of replication by imitation
            new_strategies[agent.unique_id], switches = self.determine_new_strategy(agent, other, switches)

            # keep track of surplus and quantity
            surplus_agents[agent.unique_id] = agent.surplus
            quantity_agents[agent.unique_id] = agent.quantity

        # replace each agent by its new strategy
        self.replace_agents(new_strategies, surplus_agents, quantity_agents)

        # update the amount of period sequence with no switches
        if switches > 0:
            self.model.periods_no_switches = 0
        else:
            self.model.periods_no_switches += 1

        self.time = 0
        self.steps = 0

class EvoImitationMayority(EvoRandomGS):
    """
    Scheduler for an evolutionary CDA tournament. The evolutionary process is 
    done by means of "mayority imitation".
    """

    def calc_market_average(self):
        """
        Determines the 
        """
        pass

    def reset_agents(self):
        pass