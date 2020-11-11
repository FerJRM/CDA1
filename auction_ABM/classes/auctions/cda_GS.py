#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Description of file

Name developers
"""

from mesa import Model
from mesa.time import RandomActivation

class CDA(Model):
    """
    Continuous Double Auction model as represented in Gode en Sunder (1993).
    It manages the flow in of agents steps and collects the necessary data,
    """
    def __init__(self):
        pass