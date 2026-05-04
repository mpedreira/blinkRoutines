#!/usr/bin/env python3
# pylint: disable=C0301
# -*- coding: utf-8 -*-
"""Module for static configuration of Blink + Azure Face"""

from app.classes.adapters.config_aws import ConfigAWS


class ConfigAzure(ConfigAWS):
    """Extends ConfigAWS with Azure Face API credentials."""

    def __init__(self):
        super().__init__()
        self.auth['azure_face_key'] = self.__get_parameter__('azure_face_key', '')
        self.endpoints['AZURE_FACE'] = self.__get_parameter__('azure_face_endpoint', '')
        self.azure_person_group_id = self.__get_parameter__(
            'azure_face_person_group_id', 'familia'
        )
