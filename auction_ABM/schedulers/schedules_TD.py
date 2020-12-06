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

    def step(self):
        """
        Executes the steps of all agents, one at a time, in random order. 
        Note that it is possible that none of the agents is selected. If so, 
        no action takes place.

        The function returns True if a transaction has been made, otherwise False
        """
        for agent in self.agent_buffer(shuffled=True):

            agent.set_activity(), agent.set_in_market()
            if agent.is_active() and agent.is_in_market():

                self.model.agent_last_offer = agent
                offer = agent.step()
                self.model.update_best_price(agent)

                if self.model.is_trade_possbile():
                    