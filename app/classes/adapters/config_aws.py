#!/usr/bin/env python3
# pylint: disable=C0301
# -*- coding: utf-8 -*-
"""Module for static configuration of Blink"""

import os
import shutil
import json
from app.classes.config import Config

# Bundled read-only copy (inside the zip in Lambda, or repo root locally)
_BASE_DIR = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
_BUNDLED_CONFIG = os.path.join(_BASE_DIR, "config", "config.ini")

# Runtime writable copy: /tmp in Lambda (writable), same file locally
_TMP_CONFIG = "/tmp/blink_config.ini" if os.path.exists(
    "/var/task") else _BUNDLED_CONFIG
CONFIGFILE = _TMP_CONFIG


def _ensure_config():
    """Copy the bundled config to /tmp on first Lambda invocation."""
    if CONFIGFILE == _BUNDLED_CONFIG:
        return  # local dev: CONFIGFILE is the source, nothing to copy
    if not os.path.exists(CONFIGFILE):
        if os.path.exists(_BUNDLED_CONFIG):
            shutil.copy2(_BUNDLED_CONFIG, CONFIGFILE)
        else:
            # config/config.ini not bundled in the zip (e.g. gitignored) – start fresh
            with open(CONFIGFILE, "w", encoding="utf-8") as _f:
                json.dump({}, _f)


class ConfigAWS (Config):  # pylint: disable=too-many-instance-attributes
    """Module for static configuration of Blink"""

    def __init__(self):
        """Init method for Config when you run this code in your local machine.
        """
        self.args = {}
        self.endpoints = {}
        self.auth = {}
        self.auth['USER'] = self.__get_parameter__('blink_user', '')
        self.auth['PASSWORD'] = self.__get_parameter__('blink_password', '')
        self.session = {}
        self.session['TIER'] = self.__get_parameter__(
            'blink_tier', 'prod')
        cameras_raw = self.__get_parameter__('cameras', {})
        self.cameras = cameras_raw if isinstance(
            cameras_raw, dict) else json.loads(cameras_raw)
        self.session['ACCOUNT_ID'] = self.__get_parameter__(
            'blink_account_id', '')
        self.session['CLIENT_NAME'] = 'Lambda AWS'
        self.session['TOKEN_AUTH'] = self.__get_parameter__(
            'blink_token_auth')
        self.session['REFRESH_TOKEN'] = self.__get_parameter__(
            'blink_refresh_token')
        self.session['CLIENT_ID'] = self.__get_parameter__(
            'blink_client_id', '')
        self.auth['TELEGRAM_API'] = self.__get_parameter__(
            'telegram_api_token', '')
        self.endpoints['TELEGRAM_BASEPATH'] = "https://api.telegram.org/bot"
        self.session['UID'] = self.__get_parameter__('blink_hardware_id', '')
        tier = self.session['TIER']
        self.endpoints['BLINK'] = f"https://rest-{tier}.immedia-semi.com"
        self.timeout = 3
        self.auth['aws_access_key_id'] = self.__get_parameter__(
            'aws_access_key_id', '')
        self.auth['aws_secret_access_key'] = self.__get_parameter__(
            'aws_secret_access_key', '')
        self.auth['region_name'] = self.__get_parameter__(
            'aws_region', 'us-east-1')
        self.bucket = self.__get_parameter__('aws_bucket', '')
        self.folder = self.__get_parameter__('aws_folder', '')
        self.table = self.__get_parameter__('aws_table', '')
        spotify_podcasts_raw = self.__get_parameter__('spotify_podcasts', [])
        self.spotify = {
            'client_id': self.__get_parameter__('spotify_client_id', ''),
            'client_secret': self.__get_parameter__('spotify_client_secret', ''),
            'refresh_token': self.__get_parameter__('spotify_refresh_token', ''),
            'device_id': self.__get_parameter__('spotify_device_id', ''),
            'queue_playlist_id': self.__get_parameter__(
                'spotify_queue_playlist_id', ''),
            'podcasts': spotify_podcasts_raw if isinstance(
                spotify_podcasts_raw, list) else json.loads(spotify_podcasts_raw),
            'queue_uris': self.__get_parameter__('spotify_queue_uris', []),
        }

    def set_spotify_queue(self, uris):
        """Persist the pre-built Spotify episode URIs for later playback."""
        self.__set_parameter__('spotify_queue_uris', uris, 'list')
        self.spotify['queue_uris'] = uris

    def update_tier_info(self, tier, account_id):
        """
            Persist TIER and ACCOUNT_ID to config file after a successful login.
        """
        if tier:
            self.__set_parameter__('blink_tier', tier, 'String')
            self.session['TIER'] = tier
        if account_id:
            self.__set_parameter__(
                'blink_account_id', str(account_id), 'String')
            self.session['ACCOUNT_ID'] = str(account_id)

    def update_token_auth(self, response):
        """
            Update the token(s) in the config file.
        """
        access_token = response['access_token']
        self.__set_parameter__('blink_token_auth', access_token, "String")
        self.session['TOKEN_AUTH'] = access_token
        refresh_token = response.get('refresh_token')
        if refresh_token:
            self.__set_parameter__('blink_refresh_token',
                                   refresh_token, "String")
            self.session['REFRESH_TOKEN'] = refresh_token
        return True

    def save_oauth_state(self, code_verifier, csrf_token, cookies):
        """
            Persist intermediate PKCE state between /get_basic_config and /send_2fa.
        """
        self.__set_parameter__('oauth_code_verifier', code_verifier, 'String')
        self.__set_parameter__('oauth_csrf_token', csrf_token, 'String')
        self.__set_parameter__('oauth_cookies', cookies, 'dict')

    def load_oauth_state(self):
        """
            Load intermediate PKCE state saved by save_oauth_state.
        """
        return {
            'code_verifier': self.__get_parameter__('oauth_code_verifier'),
            'csrf_token': self.__get_parameter__('oauth_csrf_token'),
            'cookies': self.__get_parameter__('oauth_cookies', {}),
        }

    def __get_parameter__(self, parameter, default=''):
        _ensure_config()
        with open(CONFIGFILE, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data.get(parameter, default)

    def __set_parameter__(self, parameter, value, value_type):
        _ensure_config()
        with open(CONFIGFILE, "r", encoding="utf-8") as file:
            data = json.load(file)
        if value_type == "String":
            data[parameter] = str(value)
        else:
            data[parameter] = value
        with open(CONFIGFILE, "w", encoding="utf-8") as file:
            json.dump(data, file)
        return True
