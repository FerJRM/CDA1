#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Description of file

Name developers
"""

import os
from multiprocessing import Pool, cpu_count

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import auction_ABM.auctions.cda_GS as GS
import auction_ABM.auctions.cda_TD as TD

DPI = 300

plt.style.use("seaborn-darkgrid")

class CDARunner:
    """
    Object to manage multiple runs in parallel for a specific set of parameters.
    """
    def __init__(self, run_name, cda_type, N, parameters, save_output=True):
        """
        Initialize runner
        """
        self.cda_type = cda_type
        self.N = N
        self.parameters = parameters
        self.save_output = save_output

        name, market_id, _, _, eq, params_model, _, _, _, _, _ = parameters
        self.eq = eq
        self.params_model = params_model
        folder = os.path.join("results", "data", name)
        os.makedirs(folder, exist_ok=True)
        self.filename = os.path.join(folder, "{}_market_{}".format(run_name,market_id))

    def run_auction(self, parameters):
        """
        Custom function to intialize a single auction object for a given set of 
        parameters and to run a single simulation.
        """
        if self.cda_type.lower() == "gs":
            auction = GS.CDA(*parameters)
        elif self.cda_type.lower() == "gs evo":
            auction = GS.EvoCDA(*parameters)
        elif self.cda_type.lower() == "TD":
            auction = TD.CDA(*parameters)
            
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
            dataframes = self.save_data(pool_results)
            df_transactions = dataframes[0]
            df_periods = dataframes[1]
            df_agents = dataframes[2]
            df_periods_agents = dataframes[3]

            if self.cda_type == "evo cda":
                df_evo = dataframes[4]
                print(df_evo)

            self.plot_price_convergence(df_transactions)
            self.analyze_rmsd_prices(df_transactions)
            mean_efficiency, mean_trade = self.efficiency_periods(df_periods)

            ## ADJUST THE PROFIT DISPERSION BECAUSE DF ONLY HAS INFO ABOUT THE LAST PERIOD
            mean_profit_dispersion = self.profit_dispersion(df_periods_agents)

            self.equilibrium_stats(df_periods, mean_efficiency, mean_trade, mean_profit_dispersion)

    def save_data(self, pool_results):
        """
        Save data of all simulations to csv file
        """

        # seperate the data gathered from the simulations into different dataframes
        data_transactions = [result[0] for result in pool_results]
        data_periods = [result[1] for result in pool_results]
        data_agents = [result[2] for result in pool_results]
        data_periods_agents = [result[3] for result in pool_results]
        df_transactions = pd.concat(data_transactions)
        df_periods = pd.concat(data_periods)
        df_agents = pd.concat(data_agents)
        df_periods_agents = pd.concat(data_periods_agents)

        if self.cda_type == "evo cda":
            data_evo = [result[4] for result in pool_results]
            df_evo = pd.concat(data_evo)
            name = self.filename + "evo_process.csv"
            df_evo.to_csv(name)

        # save transactions to csv
        name = self.filename + "_transactions.csv"
        df_transactions.to_csv(name)

        # save end-of-period data to csv
        name = self.filename + "_periods.csv"
        df_periods.to_csv(name)

        # save data agents to csv
        name = self.filename + "_agents.csv"
        df_agents.to_csv(name)

        # save data agents end of period
        name = self.filename + "_periods_agents.csv"
        df_periods_agents.to_csv(name)

        if self.cda_type == "evo cda":
            return df_transactions, df_periods, df_agents, df_periods_agents, df_evo

        return df_transactions, df_periods, df_agents, df_periods_agents

    def plot_price_convergence(self, df_transactions):
        """
        Randomly selects one of the simulations to plot
        """

        # select data of a random simulation
        random_sim = np.random.randint(0, self.N)
        df = df_transactions[df_transactions["ID"] == random_sim]
        name = self.filename + "_price_convergence.pdf"

        # plot price convergence for each period
        df = df.groupby("Period")
        fig, axes = plt.subplots(ncols=df.ngroups, sharey=True, figsize=(15,3))
        for i, (period, d) in enumerate(df):
            ax = d.plot(x="Time", y="Price", ax=axes[i], title="Period {}".format(i + 1))
            ax.axhline(self.eq[0], 0, self.params_model["total_time"], c="k", ls="--", lw=0.5)
            ax.set_xlim(0, self.params_model["total_time"])
            ax.set_ylim(self.params_model["min_price"] - 1, self.params_model["max_price"])
            ax.legend().remove()
        fig.tight_layout()

        # save figure and then close it
        fig.savefig(name, dpi=DPI)
        plt.close()

    def analyze_rmsd_prices(self, df_transactions):
        """
        Plots the root mean squared deviation of the transaciton prices across
        the quantity traded. Also saves the mean values to a csv
        """

        # try to retrieve the squared error
        df_trans_grouped = df_transactions.groupby("Quantity")
        rmse_mean = np.sqrt(df_trans_grouped["Squared error"].mean())

        # save mean rmsd and make plot
        rmse_mean.to_csv(self.filename + "_rmsd_prices.csv")
        rmse_mean.plot(
            x="Quantity", 
            y="Squared error", 
            title="Root Mean Squared Deviation of transaction prices"
        )
        plt.ylabel("Root Mean Squared Deviation")
        plt.savefig(self.filename + "_rmsd_prices.pdf", dpi=DPI)
        plt.close()

    def efficiency_periods(self, df_periods):
        """
        Saves the mean allocative efficiency across the periods and determines 
        the overall mean allocative efficiency
        """
        mean_efficiency = df_periods["Efficiency"].mean()
        df_periods_grouped = df_periods.groupby("Period")
        mean_efficiency_periods = df_periods_grouped["Efficiency"].mean()
        mean_efficiency_periods.to_csv(self.filename + "_efficiency_periods.csv")

        mean_trade = df_periods["Trade ratio"].mean()
        mean_trade_periods = df_periods_grouped["Trade ratio"].mean()
        mean_trade_periods.to_csv(self.filename + "_traderatio_periods.csv")

        # determine y-limits
        mean_efficiency_periods *= 100
        mean_trade_periods *= 100
        min_eff, max_eff = min(mean_efficiency_periods), max(mean_efficiency_periods)
        min_trade, max_trade = min(mean_trade_periods), max(mean_trade_periods)

        min_y = round(min_eff) - 10 if min_eff < min_trade else round(min_trade) - 10
        max_y = round(max_eff) + 10 if max_eff > max_trade else round(max_trade) + 10

        # make plot
        fig = plt.figure()
        mean_efficiency_periods.plot(
            x="Period",
            y="Efficiency",
            label="Efficiency"
        )
        mean_trade_periods.plot(
            x="Periods", 
            y="Trade ratio",
            label="Trade ratio"
        )
        plt.ylabel("Percentage")
        plt.xticks(mean_efficiency_periods.index)
        plt.ylim(min_y, max_y)
        plt.legend()
        plt.title("Periodwise allocative efficency and trade ratio")
        fig.savefig(self.filename + "_efficiency_periods.pdf", dpi=DPI)
        plt.close(fig)

        return mean_efficiency, mean_trade

    def profit_dispersion(self, df_periods_agents):
        """
        Determinse the mean profit disperion periodwise and over all periods
        """
        df_grouped = df_periods_agents.groupby(["ID", "Period"])
        mean_dispersion_agents = df_grouped["Profit dispersion"].mean()
        mean_dispersion_periods = np.sqrt(mean_dispersion_agents.groupby("Period").mean())

        mean_dispersion_periods.to_csv(self.filename + "_profitdispersion_periods.csv")
        mean_profit_dispersion = mean_dispersion_periods.mean()

        return mean_profit_dispersion

    def equilibrium_stats(self, df_periods, mean_efficiency, mean_trade, mean_profit_dispersion):
        """
        """
        mean_spearman = df_periods["Spearman Correlation"].mean()
        mean_spearman_pvalue = df_periods["Spearman P-value"].mean()
        
        name = self.filename + "_general_stats.txt"
        with open(name, 'w') as f:
            f.write("efficiency={}\n".format(round(mean_efficiency, 3)))
            f.write("trade ratio={}\n".format(round(mean_trade, 2)))
            f.write("profit dispersion={}\n".format(round(mean_profit_dispersion, 2)))
            f.write("spearman correlation={}\n".format(round(mean_spearman, 3)))
            f.write("spearman p-value={}\n".format(round(mean_spearman_pvalue, 3)))