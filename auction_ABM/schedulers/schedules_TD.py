#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Description of file

Name developers
"""

import random

from mesa.time import BaseScheduler

from auction_ABM.agents.buyers_TD import ZI_C_buy, Kaplan_buy, ZIP_buy
from auction_ABM.agents.sellers_TD import ZI_C_sell, Kaplan_sell, ZIP_sell

class RandomTD(BaseScheduler):
    """
    Random scheduler for the simulations based on Gode and Sunder their research.
    """

    def get_agent(self, unique_id):
        """
        Returns the agent for the given id
        """
        return self._agents[unique_id]

    def update_params_agents(self, step_over, trade_made):
        """
        Update paramater of agents at the and of a time step
        """
        for agent in self.agent_buffer():
            agent.update_params(step_over, trade_made)

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

    def step(self):
        """
        Executes the steps of all (active) agents, one at a time, in random order. 

        The function returns True if a transaction has been made, otherwise False
        """
        trade_made, trade_combos = False, []
        for agent in self.agent_buffer(shuffled=True):
            
            self.model.transaction_possible = False
            agent.set_activity(), agent.set_in_market()

            if agent.is_active() and agent.is_in_market() and random.random() < self.model.activation:

                _ = agent.step()

                if self.model.is_trade_possible(agent):
                    self.model.transaction_possible = True
                    trade_combo = self.model.make_trade(agent)
                    trade_combos.append(trade_combo)
                    trade_made = True
                    self.model.datacollector_transactions.collect(self.model)
                else:
                    self.model.update_best_price(agent)

                self.update_params_agents(False, trade_made)

        for (buyer_id, seller_id) in trade_combos:
            self.update_no_transactions(buyer_id=buyer_id, seller_id=seller_id)

        self.update_params_agents(True, trade_made)

        # update time and steps of auction
        self.steps += 1
        self.time += 1

        return trade_made