#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Description of file

Name developers
"""

import random

from mesa.time import BaseScheduler

class RandomGS(BaseScheduler):
    """
    Random scheduler for the simulations based on Gode and Sunder their research.
    """

    def get_agent(self, unique_id):
        """
        Returns the agent for the given id
        """
        return self._agents[unique_id]

    def get_active_agent(self):
        """
        Randomize agents and subsequently chooses first agents that is in market 
        and active.
        """
        for agent in self.agent_buffer(shuffled=True):
            agent.set_activity(), agent.set_in_market()
            if agent.is_active() and agent.is_in_market():
                return agent
        return None

    def reset_offers_agents(self):
        """
        Reset offers agents to intial value.
        """
        for agent in self.agent_buffer():
            agent.reset_offer()

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
        Executes the steps of all agents, one at a time, in random order. 
        Note that it is possible that none of the agents is selected. If so, 
        no action takes place.

        The function returns True if a transaction has been made, otherwise False
        """

        # only perform step if actie agent is selected
        agent, transaction_made = self.get_active_agent(), False
        if agent is not None:
            
            # update log
            if self.model.log:
                self.model.log_auction.info("BEFORE STEP AGENT")
                self.model.log_auction.info(agent.get_info())

            # perform agent's step
            agent.step()

            # update log
            if self.model.log:
                self.model.log_auction.info("AFTER STEP AGENT")
                self.model.log_auction.info(agent.get_info())

            # determines if trade needs to be made or outstanding bid/ask 
            # should be updated
            if self.model.is_trade_possible(agent):
                self.model.make_trade(agent)
                self.reset_offers_agents()
                transaction_made = True
            else:
                self.model.update_best_price(agent)

        # update time and steps of auction
        self.steps += 1
        self.time += 1
        
        return transaction_made