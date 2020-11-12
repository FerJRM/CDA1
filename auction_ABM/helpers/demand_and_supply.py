#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Description of file

Name developers
"""

import os
import random

import matplotlib.pyplot as plt
import numpy as np

def load_demand_supply(filename):
    """
    Loads demand and supply schedule from text file into lists
    """
    prices_buy, prices_sell = [], []
    with open(filename, 'r') as f:
        line = f.readline().rstrip("\n")
        line = f.readline().rstrip("\n")
        
        while line != "":
            buy, sell = line.split("\t")
            prices_buy.append(int(buy)), prices_sell.append(int(sell))
            line = f.readline().rstrip("\n")

    return prices_buy, prices_sell

def generate_random_DS(min_limit, max_limit, total_buyers, total_sellers, commodities):
    """
    Generates demand and supply for a double auction by means of induced value theory
    """
    eq = ()
    while len(eq) == 0 or 0 in eq:
        prices = random_limit_prices(min_limit, max_limit, total_buyers, total_sellers, commodities)
        prices_buy, prices_sell, all_prices_buy, all_prices_sell = prices

        eq = determine_equilibrium(prices_buy, prices_sell, all_prices_buy, all_prices_sell)

    return prices_buy, prices_sell, all_prices_buy, all_prices_sell, eq

def random_limit_prices(min_price, max_price, total_buyers, total_sellers, commodities):
    """
    Generates a set of random limit prices by means of the induces value theorem
    of V. Smith (1976). Note, it makes sure that at least one of the commodities
    can be traded.
    """

    # generate limit prices untill they are valid (trades are possible)
    valid_prices = False
    while not valid_prices:

        # generate random limit prices and sort them
        prices_buy = [random.randint(min_price, max_price) for _ in range(commodities)]
        prices_sell = [random.randint(min_price, max_price) for _ in range(commodities)]
        prices_buy.sort(reverse=True), prices_sell.sort()
        valid_prices = is_valid_prices(prices_buy, prices_sell, commodities)

    # generate prices list for demand and supply schedule
    all_prices_buy, all_prices_sell = prices_buy * total_buyers, prices_sell * total_sellers
    all_prices_buy.sort(reverse=True)
    all_prices_sell.sort()
    
    return prices_buy, prices_sell, all_prices_buy, all_prices_sell

def is_valid_prices(prices_buy, prices_sell, commodities):
    """
    Checks if any trades are possible. If so it make sure 
    only one unique equilibrium exists by ensuring a common price for the buyers
    and sellers.
    """

    # ensures that at least one trade is possible
    min_sell, max_buy = min(prices_sell), max(prices_buy)
    if min_sell >= max_buy:
        return False

    # ensures a common price (equilibrium) price
    for commodity in range(commodities):

        # if price to buy become lower that price to sell it means then it means
        # afterwards nog trades are possible so we make this our equilibrium point
        if prices_buy[commodity] <= prices_sell[commodity] and commodity != commodities - 1:

            # makes sure a valid equilibrium price  is inserted, so that the
            # demand and supply are still resp decreasing and increasing
            if prices_buy[commodity] >= prices_sell[commodity - 1]:
                prices_sell[commodity] = prices_buy[commodity]
            elif prices_sell[commodity] <= prices_buy[commodity - 1]:
                prices_buy[commodity] = prices_sell[commodity]
            else:
                prices_buy[commodity] = prices_sell[commodity - 1]
                prices_sell[commodity] = prices_sell[commodity - 1]
                
            return True

    return False

def demand(p, valuations):
    """
    Represententation of a demand function. It returns the quantity demanded for 
    a product with a given price and a given set of valuations ordered 
    from highest-to-lowest.
    """
    quantity = 0
    for valuation in valuations:
        if p <= valuation:
            quantity += 1
        else:
            break

    return quantity

def supply(p, valuations):
    """
    Represententation of a supply function. It returns the quantity supplied for 
    a product with a given price and a given set of valuations ordered 
    from lowest-to-highest.
    """
    quantity = 0
    for valuation in valuations:
        if p >= valuation:
            quantity += 1
        else:
            break
    
    return quantity

def demand_minus_supply(p, all_prices_buy, all_prices_sell):
    """
    Represents excess demand function.
    """
    return demand(p, all_prices_buy) - supply(p, all_prices_sell)

def determine_equilibrium(prices_buy, prices_sell, all_prices_buy, all_prices_sell):
    """
    Determines the equlibrium for given sets of valuations
    """
    for i, (buy, sell) in enumerate(zip(prices_buy, prices_sell)):
        excess_demand_buy = demand_minus_supply(buy, all_prices_buy, all_prices_sell)
        excess_demand_sell = demand_minus_supply(sell, all_prices_buy, all_prices_sell)

        if excess_demand_buy >= 0:
            q = demand(buy, all_prices_buy)
            surplus = buy * q
            return buy, demand(buy, all_prices_buy), surplus

    return ()

def save_prices(prices_buy, prices_sell, equilibrium, folder, market_id):
    """
    Saves the limit prices tot text file, so it can be re-used
    """
    os.makedirs(folder, exist_ok=True)
    filename = os.path.join(folder, "market_" + str(market_id) + ".txt")
    with open(filename, 'w') as f:
        f.write("BUY\tSELL\n")
        for buy, sell in zip(prices_buy, prices_sell):
            f.write("{}\t{}\n".format(buy, sell))

    filename = os.path.join(folder, "equilbrium_market_" + str(market_id) + ".txt")
    with open(filename, 'w') as f:
        price, quantity, surplus = equilibrium
        f.write("Price\t{}\n".format(price))
        f.write("Quantity\t{}\n".format(quantity))
        f.write("Surplus\t{}\n".format(surplus))


def plot_demand_supply(
        prices_buy, prices_sell, all_prices_buy, all_prices_sell, 
        total_buyers, total_sellers, commodities, min_poss_price, max_poss_price, 
        folder, market_id, show_plot=True, save_plot=False
    ):
    """
    Plots demand and supply scedule for a given set of prices
    """

    # make sure folder exists, prepare name, and quantities for plot
    os.makedirs(folder, exist_ok=True)
    filename = os.path.join(folder, "market_" + str(market_id) + ".pdf")
    q_demand = [demand(p, all_prices_buy) for p in prices_buy]
    q_supply = [supply(p, all_prices_sell) for p in prices_sell]

    # extand last value so the plot will be a bit more smoothned
    q_demand.append(q_demand[-1] + total_buyers)
    prices_buy_copy = prices_buy + [prices_buy[-1]]
    q_supply.append(q_supply[-1] + total_sellers)
    prices_sell_copy = prices_sell + [prices_sell[-1]]

    # plot figure
    fig = plt.figure()
    plt.step(q_demand, prices_buy_copy, where="post", label="Demand")
    plt.step(q_supply, prices_sell_copy, where="post", label="Supply")

    # determine ticks for labels
    if total_buyers <= total_sellers:
        plt.xticks([(x + 1) * total_buyers for x in range(commodities + 1)])
    else:
        plt.xticks([(x + 1) * total_sellers for x in range(commodities + 1)])
    step = (max_poss_price - min_poss_price) // 5
    plt.yticks(list(range(min_poss_price, max_poss_price + step, step)))

    # add labels to axis and legend to plot
    plt.xlabel("Quantity")
    plt.ylabel("Price")
    plt.title("Demand and supply curve for market {}".format(market_id))
    plt.legend()

    if save_plot:
        fig.savefig(filename, dpi=300)

    if show_plot:
        plt.show()

    plt.close(fig)