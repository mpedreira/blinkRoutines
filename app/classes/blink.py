#!/usr/bin/env python3
# pylint: disable=R0903
# -*- coding: utf-8 -*-
"""Module for Blink"""


class Blink ():
    """ Intending of following Hexagonal Architecture, this class is the core"""

    def __init__(self, config):
        """
        Init method for BlinkAPI

        Args:
            config (class): 
                This parameter includes the configuration needed for use this module.
                It is defined in config_WHATEVER.py in adapters folder

        Returns:
            None: 
        """
        self.config = config
        self.server = self.config.endpoints['BLINK']
        self.client_id = ''
        self.account_id = ''
        self.token_auth = ''
        self.basic_info = {}
        self.basic_info['account'] = {}
        self.basic_info['account']['tier'] = 'prod'

    def get_client_id(self):
        """
            Taking the basic information of the blink account, 
            gets the client ID

        Returns:
            int: Returns the client_id that is the identification of 
            the aplication in the blink account
        """
        self.client_id = self.basic_info['account']['client_id']
        return self.client_id

    def get_account_id(self):
        """
            Taking the basic information of the blink account,
            gets the account ID

        Returns:
           int : Returns the account_id that is the identification of
              the account in the blink account
        """
        self.account_id = self.basic_info['account']['account_id']
        return self.account_id

    def get_token_auth(self):
        """
            Taking the basic information of the blink account,
            gets the token auth
        Returns:
            str: Returns de API token for the client
        """
        self.token_auth = self.basic_info['auth']['token']
        return self.token_auth

    def set_client_id(self, client_id):
        """
            Sets the client ID

        Args:
            clientID (str): Once you have the client ID, you dont need to 
             re-login(with 2FA) again until the token expires. You can use
             the one you created

        Returns:
            str: Returns the client_id defined
        """
        self.client_id = client_id
        return self.client_id

    def set_token_auth(self, token_auth):
        """
            Sets the token auth

        Args:
            token_auth (str): Once you have the token_auth, you dont need to 
             re-login(with 2FA) again until the token expires. You can use
             the one you created

        Returns:
            str: Returns the token_auth defined
        """
        self.token_auth = token_auth
        return self.token_auth

    def set_account_id(self, account_id):
        """
            Sets the account ID

        Args:
            accountID (str): Once you have the account ID, you dont need to 
             re-login(with 2FA) again until the token expires. You can use
             the one you created

        Returns:
            str: Returns the account_id defined
        """
        self.account_id = account_id
        return self.account_id

    def set_tier(self, tier):
        """
            Sets the tier of the account

        Args:
            tier (str): Tier defined in the basic information of the account

        Returns:
            str: Returns the tier defined
        """
        self.basic_info['account']['tier'] = tier
        return self.basic_info['account']['tier']

    def get_server(self):
        """
            Gets the server for the account

        Returns:
            str: returns the uri where you should do the requests
        """
        tier = self.basic_info['account']['tier']
        self.server = self.server.replace('prod', tier)
        return self.server
