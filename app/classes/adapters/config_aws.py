#!/usr/bin/env python3
# pylint: disable=C0301,R0903,E0401
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
        self.cameras = json.loads(os.environ['CAMERAS'])
        self.auth['USER'] = os.environ['USER']
        self.auth['PASSWORD'] = os.environ['PASSWORD']
        self.session['TIER'] = os.environ['TIER']
        self.auth['TELEGRAM_API'] = os.environ['TELEGRAM_API']
        self.endpoints['TELEGRAM_BASEPATH'] = os.environ['TELEGRAM_BASEPATH']
        self.session['ACCOUNT_ID'] = os.environ['ACCOUNT_ID']
        self.parameter_store = os.environ['PARAMETER_STORE']
        self.session['TOKEN_AUTH'] = self.__get_parameter__(
            "blink_token_auth")
        self.session['CLIENT_ID'] = os.environ['CLIENT_ID']
        self.session['CLIENT_NAME'] = os.environ['CLIENT_NAME']
        self.session['UID'] = os.environ['UID']
        self.endpoints['BLINK'] = os.environ['BLINK_ENDPOINT']
        self.timeout = int(os.environ['TIMEOUT'])

    def update_token_auth(self, response):
        """
            Update the token in the config.
        """
        parameter = response['auth']['token']
        self.__set_parameter__(self.parameter_store, parameter, "String")
        self.session['TOKEN_AUTH'] = parameter
        return True

    def __set_parameter__(self, parameter, value, value_type):
        ssm_client = boto3.client('ssm')
        return ssm_client.put_parameter(Name=parameter, Value=value, Type=value_type, Overwrite=True)

    def __get_parameter__(self, parameter):
        ssm_client = boto3.client('ssm')
        response = ssm_client.get_parameter(
            Name=parameter, WithDecryption=True)
        return response['Parameter']['Value']
