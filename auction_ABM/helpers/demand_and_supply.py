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

def generate_random_DS(min_limit, max_limit, total_buyers, total_sellers, commodities):
    """
    Generates demand and supply for a double auction by means of induced value theory
    """
    eq = ()
    while len(eq) == 0 or 0 in eq:
        prices = random_limit_prices(min_limit, max_limit, total_buyers, total_sellers, commodities)
        prices_buy, prices_sell, all_prices_buy, all_prices_sell = prices

        eq = determine_equilibrium(prices_buy, prices_sell, all_prices_buy, all_prices_sell, total_buyers, total_sellers)

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
        # afterwards no trades are possible so we make this our equilibrium point
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

def determine_equilibrium(prices_buy, prices_sell, all_prices_buy, all_prices_sell, total_buyers, total_sellers):
    """
    Determines the equlibrium for given sets of valuations
    """

    # variable to keep track of surplus of market and others to assist in
    # calculation equilibrium
    surplus = 0
    prev_buy, prev_sell = 0, 0
    prev_buy_left, prev_sell_left = 0, 0

    # start calculation following the Marshalian path
    for i, (buy, sell) in enumerate(zip(prices_buy, prices_sell)):
        excess_demand_buy = demand_minus_supply(buy, all_prices_buy, all_prices_sell)
        
        # if more buyers than sellers make sure that previous buyers sell their
        # commodities first; keep track for next commodities
        if total_buyers > total_sellers:
            if prev_buy_left > 0:
                surplus += (prev_buy - sell) * prev_buy_left

            trades = total_sellers - prev_buy_left
            prev_buy_left = total_buyers - trades
            prev_buy = buy
        
        # if equal amoun or more sellers (same story as above)
        else:
            if prev_sell_left > 0:
                surplus += (buy - prev_sell) * prev_sell_left

            trades = total_buyers - prev_sell_left
            prev_sell_left = total_sellers - trades
            prev_sell = sell

        # update surplus market
        surplus += (buy - sell) * trades

        # crosspoint demand and supply found, so equilbrium found and search can be stopped
        if excess_demand_buy >= 0:
            q = demand(buy, all_prices_buy)

            # determine equilbrium surplus for a buyer and seller in the market
            buy_surplus, sell_surplus = 0, 0
            for commodity in range(i + 1):
                buy_surplus += prices_buy[commodity] - buy
                sell_surplus += buy - prices_sell[commodity]

            # return equilibrium values
            return buy, q, surplus, buy_surplus, sell_surplus

    # return empty equilibrium value, if something might have gone wrong
    return ()

def save_prices(prices_buy, prices_sell, equilibrium, market_name, market_id):
    """
    Saves the limit prices tot text file, so it can be re-used
    """

    # save individual demand and supply schedules (limit prices) to text file
    folder = os.path.join("{}_market_{}".format(market_name, market_id))
    filename = os.path.join(folder, "market.txt")
    with open(filename, 'w') as f:
        f.write("BUY\tSELL\n")
        for buy, sell in zip(prices_buy, prices_sell):
            f.write("{}\t{}\n".format(buy, sell))

    # save equilbrium values to text file
    filename = os.path.join(folder, "equilibrium_market.txt")
    with open(filename, 'w') as f:
        price, quantity, surplus, buy_surplus, sell_surplus = equilibrium
        f.write("Price\t{}\n".format(price))
        f.write("Quantity\t{}\n".format(quantity))
        f.write("Surplus\t{}\n".format(surplus))
        f.write("Buyer surplus\t{}\n".format(buy_surplus))
        f.write("Seller surplus\t{}\n".format(sell_surplus))


def plot_demand_supply(
        prices_buy, prices_sell, all_prices_buy, all_prices_sell, 
        total_buyers, total_sellers, commodities, min_poss_price, max_poss_price, 
        market_name, market_id, show_plot=True, save_plot=False
    ):
    """
    Plots demand and supply scedule for a given set of prices
    """

    # make sure folder exists, prepare name, and quantities for plot
    folder = os.path.join("{}_market_{}".format(market_name, market_id))
    os.makedirs(folder, exist_ok=True)
    filename = os.path.join(folder, "market.pdf")
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

    # determine xticks for labels
    if total_buyers <= total_sellers:
        plt.xticks([(x + 1) * total_buyers for x in range(commodities + 1)])
    else:
        plt.xticks([(x + 1) * total_sellers for x in range(commodities + 1)])
    
    # determine yticks for labels
    if min_poss_price == 1:
        step = (max_poss_price - 0) // 5
        plt.yticks(list(range(0, max_poss_price + step, step)))
    else:
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