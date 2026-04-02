#!/usr/bin/env python3
# pylint: disable=C0301,R0903,E0401,R0902
# -*- coding: utf-8 -*-
"""Module for static configuration of Claroty"""

import os
import json
import boto3
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
        self.auth = {}
        self.payload = {}
        self.cameras = json.loads(os.environ['CAMERAS'])
        self.auth['USER'] = os.environ['USER']
        self.auth['PASSWORD'] = os.environ['PASSWORD']
        self.session['TIER'] = os.environ['TIER']
        self.auth['TELEGRAM_API'] = os.environ['TELEGRAM_API']
        self.endpoints['TELEGRAM_BASEPATH'] = os.environ['TELEGRAM_BASEPATH']
        self.session['ACCOUNT_ID'] = os.environ['ACCOUNT_ID']
        self.parameter_store = os.environ['PARAMETER_STORE']
        self.session['TOKEN_AUTH'] = self.__get_parameter__(
            self.parameter_store)
        refresh_store = os.environ.get('REFRESH_TOKEN_PARAMETER_STORE', '')
        self.session['REFRESH_TOKEN'] = self.__get_parameter__(
            refresh_store) if refresh_store else ''
        self.session['CLIENT_ID'] = os.environ['CLIENT_ID']
        self.session['CLIENT_NAME'] = os.environ['CLIENT_NAME']
        self.session['UID'] = os.environ['UID']
        self.endpoints['BLINK'] = os.environ['BLINK_ENDPOINT']
        self.timeout = int(os.environ['TIMEOUT'])

    def update_tier_info(self, tier, account_id):
        """
            Persist TIER and ACCOUNT_ID to SSM Parameter Store after a successful login.
        """
        if tier:
            self.session['TIER'] = tier
        if account_id:
            self.session['ACCOUNT_ID'] = str(account_id)

    def update_token_auth(self, response):
        """
            Update the token(s) in AWS SSM Parameter Store.
        """
        access_token = response['access_token']
        self.__set_parameter__(self.parameter_store, access_token, "String")
        self.session['TOKEN_AUTH'] = access_token
        refresh_token = response.get('refresh_token')
        if refresh_token:
            refresh_store = os.environ.get('REFRESH_TOKEN_PARAMETER_STORE', '')
            if refresh_store:
                self.__set_parameter__(refresh_store, refresh_token, "String")
            self.session['REFRESH_TOKEN'] = refresh_token
        return True

    def save_oauth_state(self, code_verifier, csrf_token, cookies):
        """
            Persist intermediate PKCE state in SSM Parameter Store.
        """
        base = self.parameter_store.rstrip('/')
        self.__set_parameter__(f'{base}_pkce_verifier',
                               code_verifier, 'String')
        self.__set_parameter__(f'{base}_pkce_csrf', csrf_token, 'String')
        import json as _j
        self.__set_parameter__(f'{base}_pkce_cookies',
                               _j.dumps(cookies), 'String')

    def load_oauth_state(self):
        """
            Load intermediate PKCE state from SSM Parameter Store.
        """
        import json as _j
        base = self.parameter_store.rstrip('/')
        try:
            cookies_raw = self.__get_parameter__(f'{base}_pkce_cookies')
            cookies = _j.loads(cookies_raw) if cookies_raw else {}
        except Exception:
            cookies = {}
        return {
            'code_verifier': self.__get_parameter__(f'{base}_pkce_verifier'),
            'csrf_token': self.__get_parameter__(f'{base}_pkce_csrf'),
            'cookies': cookies,
        }

    def __set_parameter__(self, parameter, value, value_type):
        ssm_client = boto3.client('ssm')
        return ssm_client.put_parameter(Name=parameter, Value=value, Type=value_type, Overwrite=True)

    def __get_parameter__(self, parameter):
        ssm_client = boto3.client('ssm')
        response = ssm_client.get_parameter(
            Name=parameter, WithDecryption=True)
        return response['Parameter']['Value']
