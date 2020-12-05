#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Description of file

Name developers
"""

from auction_ABM.auctions.cda_GS import * 
from auction_ABM.schedulers.schedules import EvoRandomGS

class EvoCDA(CDA):
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
                "Efficiency": allocative_efficiency,
                "Trade ratio": trade_ratio,
                "Quantity": quantity_curr_period,
                "Spearman Correlation": get_spearman_corr,
                "Spearman P-value": get_spearman_pvalue
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
        self.schedule = EvoRandomGS(self)
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
                    # other_agent = self.make_trade(agent)
                    self.reset_asks(), self.reset_bids()
                    self.schedule.reset_offers_agents()
                    self.datacollector_transactions.collect(self)
                    self.no_transactions = 0
                else:
                    self.no_transactions += 1
                    self.schedule.update_no_transactions()
                
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
            self.efficiency[self.period] = allocative_efficiency(self)
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
                print("POPULATION HAS CONVERGED")
                break

        self.running = False

        # update datacollectors with end of period information
        data_transactions = self.datacollector_transactions.get_model_vars_dataframe()
        data_periods = self.datacollector_periods.get_model_vars_dataframe()
        data_agents = self.datacollector_transactions.get_agent_vars_dataframe()
        data_periods_agents = self.datacollector_periods.get_agent_vars_dataframe()

        return data_transactions, data_periods, data_agents, data_periods_agents, pd.DataFrame(self.evo_process)