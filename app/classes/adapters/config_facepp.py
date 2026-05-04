#!/usr/bin/env python3
# pylint: disable=C0301
# -*- coding: utf-8 -*-
"""Module for static configuration of Blink + Face++ (Face Plus Plus)"""

from app.classes.adapters.config_aws import ConfigAWS


class ConfigFacePP(ConfigAWS):
    """Extends ConfigAWS with Face++ API credentials."""

    def __init__(self):
        super().__init__()
        self.auth['facepp_api_key'] = self.__get_parameter__('facepp_api_key', '')
        self.auth['facepp_api_secret'] = self.__get_parameter__('facepp_api_secret', '')
        self.endpoints['FACEPP'] = self.__get_parameter__(
            'facepp_api_url', 'https://api-us.faceplusplus.com'
        )
        self.facepp_faceset_outer_id = self.__get_parameter__(
            'facepp_faceset_outer_id', 'familia'
        )
