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
        Randomize agents and subsequently chooses first agents that is active 
        and willing too shout.
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
        Resets all agents' attributes to their intial values
        """
        for agent in self.agent_buffer():
            agent.reset_agent()

        self.time = 0
        self.steps = 0

    def step(self):
        """
        Executes the steps of all agents, one at a time, in random order
        """
        agent, transaction_made = self.get_active_agent(), False
        if agent is not None:
            # print("BEFORE STEP")
            # print(agent.get_info())
            agent.step()
            # print("AFTER")
            # print(agent.get_info())

            # check if trade is possible, if so make trade, reset agents' offers
            # and also update statistics model and of the agents trading
            if self.model.is_trade_possible(agent):
                # print("TRADE POSSIBLE!!!!!")
                self.model.make_trade(agent)
                self.reset_offers_agents()
                transaction_made = True
            else:
                self.model.update_best_price(agent)

        self.steps += 1
        self.time += 1
        
        return transaction_made