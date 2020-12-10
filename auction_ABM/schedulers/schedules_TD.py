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

class ImitationScheduler(RandomTD):
    """
    Scheduler for an evolutionary CDA tournament. The evolutionary process is 
    done by means of "replication by imitation".
    """

    def determine_new_strategy(self, agent, other, switches):
        """
        Determines if the agent decides to switch strategies or not by comparing
        its own performance to a randomly selected other trader of the same
        market side
        """

        # own profit is better, keep strategy
        if agent.surplus > other.surplus:
            return agent.strategy, switches, agent.get_import_params()

        # profit other is better, switch strategy depending on relative difference
        elif agent.surplus < other.surplus:

            prob = (other.surplus - agent.surplus) / other.surplus      
            if random.random() < prob:

                if other.strategy != agent.strategy:
                    switches += 1
                    return other.strategy, switches, other.get_import_params()
                else:
                    return agent.strategy, switches, other.get_import_params()

            else:
                return agent.strategy, switches, agent.get_import_params()

        # surplus is equal so choice depends on the quantity of both agents
        elif agent.quantity > other.quantity:
            return agent.strategy, switches, agent.get_import_params()

        elif agent.quantity < other.quantity:

            if other.strategy != agent.strategy:
                switches += 1
                return other.strategy, switches, other.get_import_params()
            else:
                return agent.strategy, switches, other.get_import_params()

        # quantity is also equal so rather test same strategy again
        else:
            return agent.strategy, switches, agent.get_import_params()

    def replace_buyer(self, agent, new_strategy, params_agent):
        """
        Replace a buyer by its new strategy, keep track of its surplus and 
        quantity and reset its parameters. Returns the newly made agent
        """

        quantity, surplus = agent.get_quantity_surplus()

        # make new agent
        standard_params = [agent.unique_id, self.model, self.model.prices_buy, self.model.eq_buyer_surplus]
        if new_strategy.upper() == "ZI_C":
            new_agent = ZI_C_buy(*standard_params)

        elif new_strategy.upper() == "KAPLAN":
            new_agent = Kaplan_buy(*standard_params, self.model.params_strats[new_strategy.upper()])

        elif new_strategy.upper() == "ZIP":
            new_agent = ZIP_buy(*standard_params, self.model.params_strats[new_strategy.upper()])

        # keep track of surplus and quantity; reset agent for next period
        new_agent.set_import_params(params_agent)
        new_agent.set_quantity_surplus(quantity, surplus)
        new_agent.reset_agent()

        return new_agent

    def replace_seller(self, agent, new_strategy, params_agent):
        """
        Replace a seller by its new strategy, keep track of its surplus and 
        quantity and reset its parameters. Returns the newly made agent
        """

        quantity, surplus = agent.get_quantity_surplus()

        # make new agent
        standard_params = [agent.unique_id, self.model, self.model.prices_sell, self.model.eq_seller_surplus]
        if new_strategy.upper() == "ZI_C":
            new_agent = ZI_C_sell(*standard_params)
        elif new_strategy.upper() == "KAPLAN":
            new_agent = Kaplan_sell(*standard_params, self.model.params_strats[new_strategy.upper()])
        elif new_strategy.upper() == "ZIP":
            new_agent = ZIP_sell(*standard_params, self.model.params_strats[new_strategy.upper()])

        # keep track of surplus and quantity; reset agent for next period
        new_agent.set_import_params(params_agent)
        new_agent.set_quantity_surplus(quantity, surplus)
        new_agent.reset_agent()

        return new_agent

    # def replace_agents(self, new_strategies, surplus_agents, quantity_agents):
    def replace_agents(self, new_strategies, params_agents):
        """
        Replace all agents by their new strategies
        """
        # replace each agent by its new strategy
        for agent in self.agent_buffer():
            if agent.market_side.lower() == "buyer":
                new_agent = self.replace_buyer(
                    agent, new_strategies[agent.unique_id], params_agents[agent.unique_id]
                )
            else:
                new_agent = self.replace_seller(
                    agent, new_strategies[agent.unique_id], params_agents[agent.unique_id]
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
        # their surplus and quantity, ALSO KEEP TRACK OF THEIR PARAMETERS
        new_strategies = {}
        params_agents = {}
        for agent in self.agent_buffer():

            # if current profit is better than last period then keep strategy
            if agent.surplus >= agent.prev_surplus:
                new_strategies[agent.unique_id] = agent.strategy
                params_agents[agent.unique_id] = agent.get_import_params()
                continue

            # randomly select other agent from same market side
            while True:
                other = self.model.random.choice(self.agents)
                if agent.market_side.upper() == other.market_side.upper():
                    break

            # determines which strategy to choose by means of replication by imitation
            new_strategies[agent.unique_id], switches, params_agents[agent.unique_id] = self.determine_new_strategy(
                agent, other, switches
            )

        # replace each agent by its new strategy
        self.replace_agents(new_strategies, params_agents)

        # update the amount of period sequence with no switches
        if switches > 0:
            self.model.periods_no_switches = 0
        else:
            self.model.periods_no_switches += 1

        self.time = 0
        self.steps = 0