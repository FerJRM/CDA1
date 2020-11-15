#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Description of file

Name developers
"""

import os
from multiprocessing import Pool, cpu_count

import pandas as pd

from classes.auctions.cda_GS import CDA

class CDARunner:
    """
    Object to manage multiple runs in parallel for a specific set of parameters.
    """
    def __init__(self, run_name, N, parameters, save_output=True):
        """
        Initialize runner
        """
        self.N = N
        self.parameters = parameters
        self.save_output = save_output

        name, market_id, _, _, _, _, _, _, _, _, _ = parameters
        folder = os.path.join("results", "data", name)
        os.makedirs(folder, exist_ok=True)
        self.filename = os.path.join(folder, "{}_market_{}".format(run_name,market_id))

    def run_auction(self, parameters):
        """
        Custom function to intialize a single auction object for a given set of 
        parameters and to run a single simulation.
        """
        auction = CDA(*parameters)
        return auction.step()

    def run_all(self):
        """
        Run all simulations in parallel.
        """
        pool = Pool(cpu_count())
        pool_input = [(n, *self.parameters) for n in range(self.N)]
        pool_results = pool.map(self.run_auction, pool_input)
        pool.close()
        pool.join()

        if self.save_output:
            self.save_data(pool_results)

    def plot_price_convergence(self):
        """
        Only plots price convergence of best and worst simulation 
        based on allocative efficiency
        """
        pass

    def determine_stats(self):
        """
        Also need stats such as root mean squared deviation of transaction prices
        from the equilibrium price averaged across the periods (transaction sequence number is x axis), 
        profit dispersion (this can be measued at the agent directly as attribute; at least the sum)
        """
        pass

    def save_data(self, results):
        """
        Save data of all simulations to csv file
        """
        data_model = [result[0] for result in results]
        data_agents = [result[1] for result in results]

        df_model = pd.concat(data_model)
        name = self.filename + "_model.csv"
        df_model.to_csv(name, 'w')
        print(df_model.head())
        print(df_model.tail())
        print("===============================================================")

        df_agents = pd.concat(data_agents)
        name = self.filename + "_agents.csv"
        df_agents.to_csv(name, 'w')
        print(df_agents.head())
        print(df_agents.tail())
        print("===============================================================")