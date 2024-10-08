#!/usr/bin/env python3
# pylint: disable=C0301,R0903
# -*- coding: utf-8 -*-
"""Module for static configuration of Claroty"""

import os
from app.classes.config import Config


class ConfigAWS (Config):
    """Module for AWS configuration of Blink"""

    def __init__(self):
        """
            Init method for Config when you run this code in AWS.
            They are recived from the environment variables.
        """
        self.endpoints = {}
        self.session = {}
        self.session['TIER'] = os.environ['TIER']
        self.session['ACCOUNT_ID'] = os.environ['ACCOUNT_ID']
        self.session['TOKEN_AUTH'] = os.environ['TOKEN_AUTH']
        self.session['CLIENT_ID'] = os.environ['CLIENT_ID']

        self.endpoints['BLINK'] = os.environ['BLINK_ENDPOINT']
        self.timeout = int(os.environ['TIMEOUT'])
