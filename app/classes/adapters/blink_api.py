#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Module for using Blink Cameras through API"""
# pylint: disable=R0904,R0801,E0401
import hashlib
import base64
import secrets
import json
from html.parser import HTMLParser
from time import sleep, time
from urllib.parse import urlencode, urlparse, parse_qs
import requests as _req
from app.classes.blink import Blink
from app.classes.adapters.http_request_standard import HttpRequestStandard

WAIT_CODE = 409
MAX_RETRIES = 5


class BlinkAuthError(RuntimeError):
    """Raised when a Blink authentication step fails."""


class BlinkOAuthError(BlinkAuthError):
    """Raised when an OAuth token exchange or refresh fails."""


class BlinkLoginError(BlinkAuthError):
    """Raised when the initial PKCE login flow fails."""


# ── OAuth v2 PKCE constants (inspired by blinkpy dev branch) ──────────────────
_OAUTH_BASE = "https://api.oauth.blink.com"
_OAUTH_V2_AUTHORIZE = f"{_OAUTH_BASE}/oauth/v2/authorize"
_OAUTH_V2_SIGNIN = f"{_OAUTH_BASE}/oauth/v2/signin"
_OAUTH_V2_2FA_VERIFY = f"{_OAUTH_BASE}/oauth/v2/2fa/verify"
_OAUTH_TOKEN_URL = f"{_OAUTH_BASE}/oauth/token"
_TIER_URL = "https://rest-prod.immedia-semi.com/api/v1/users/tier_info"
_OAUTH_V2_CLIENT_ID = "ios"        # used for auth-code + refresh grants
_OAUTH_REDIRECT_URI = "immedia-blink://applinks.blink.com/signin/callback"
_OAUTH_SCOPE = "client"
_BROWSER_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
    "Version/26.1 Mobile/15E148 Safari/604.1"
)
_TOKEN_UA = "Blink/2511191620 CFNetwork/3860.200.71 Darwin/25.1.0"


def _is_token_expired(token):
    """Decode JWT exp claim (no signature check). Returns True if expired or within 60 s."""
    try:
        payload_b64 = token.split('.')[1]
        payload_b64 += '=' * (4 - len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        return time() >= payload.get('exp', 0) - 60
    except (IndexError, ValueError, KeyError):
        return True


def _generate_pkce_pair():
    """Generate PKCE code_verifier and code_challenge (S256)."""
    code_verifier = (
        base64.urlsafe_b64encode(secrets.token_bytes(32))
        .decode("utf-8")
        .rstrip("=")
    )
    code_challenge = (
        base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode("utf-8")).digest()
        )
        .decode("utf-8")
        .rstrip("=")
    )
    return code_verifier, code_challenge


class _OAuthArgsParser(HTMLParser):
    """Extract CSRF token from <script id="oauth-args" type="application/json">."""

    def __init__(self):
        super().__init__()
        self.csrf_token = None
        self._in_script = False

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            d = dict(attrs)
            if d.get("id") == "oauth-args" and d.get("type") == "application/json":
                self._in_script = True

    def handle_data(self, data):
        if self._in_script:
            try:
                self.csrf_token = json.loads(data).get("csrf-token")
            except (json.JSONDecodeError, AttributeError):
                pass
            self._in_script = False

    def handle_endtag(self, tag):
        if tag == "script":
            self._in_script = False


def _extract_csrf(html):
    """Extract CSRF token from Blink signin page HTML."""
    parser = _OAuthArgsParser()
    parser.feed(html)
    return parser.csrf_token


class BlinkAPI (Blink):
    """
    Class for using Blink Cameras through API.
    This class is a subclass of Blink

    Args:
        Blink (class): parent class
    """

    def __set_token__(self):
        self.set_tier(self.config.session['TIER'])
        self.set_account_id(self.config.session['ACCOUNT_ID'])
        token = self.config.session['TOKEN_AUTH']
        if _is_token_expired(token):
            try:
                self.__oauth_refresh__()
            except BlinkOAuthError as exc:
                raise RuntimeError(
                    'Access token expired and refresh failed. '
                    'Re-authenticate via POST /get_basic_config.'
                ) from exc
        else:
            self.set_token_auth(token)
        self.set_client_id(self.config.session['CLIENT_ID'])

    def __prepare_http_request__(self):
        """
            The http requests are almost the same in this integration
            with this method we prepare the payload for the request

        Returns:
            list: returns the payload required for http request
        """
        payload = {}
        payload['config'] = self.config
        payload['headers'] = {
            'Content-Type': 'application/json'
        }
        payload['timeout'] = self.config.timeout
        payload['data'] = ''
        payload['auth'] = ''
        return payload

    def arm_network(self, network_id):
        """
            Set to arm one network

        Args:
            network_id (str): is the identification of the network
            you want to arm

        Returns:
            list: returns the response of the server to the request
        """
        payload = self.__prepare_http_request__()
        payload['headers']['Authorization'] = "Bearer " + self.token_auth
        payload['headers']['hardware_id'] = self.config.session['UID']

        endpoint = {}
        endpoint['uri'] = self.server + '/api/v1/accounts/' + \
            self.account_id + '/networks/' + network_id + '/state/arm'
        endpoint['certificate'] = False
        http_instance = HttpRequestStandard(endpoint, payload)
        http_instance.post_request()
        if http_instance.is_ok_response():
            people = int(self.config.__get_parameter__(
                "blink_number_of_people_"+str(network_id)))
            people += 1
            self.config.__set_parameter__("blink_number_of_people_"+str(network_id),
                                          str(people), "String")
        return self.__get_response_to_request__(http_instance)

    def __get_response_to_request__(self, http_instance):
        """
        Args:
            http_instance (class): this is the class used for the http request

        Returns:
            list: returns a json file with the status_code of the server, if the
            response is ok or not and the response of the server. If the response is
            not a json, it returns the text without format
        """
        result = {}
        result['status_code'] = http_instance.response.status_code
        result['is_ok'] = http_instance.is_ok_response()
        try:
            result['response'] = json.loads(http_instance.response.text)
        except json.decoder.JSONDecodeError:
            result['response'] = {"message": http_instance.response.text}
        return result

    def get_clip(self, clip_id):
        """
            Gets a clip from the server

        Args:
            clip_id (str): path of the clip

        Returns:
            bytes: returns the clip in mp4 format
        """
        payload = self.__prepare_http_request__()
        payload['headers']['Authorization'] = "Bearer " + self.token_auth
        endpoint = {}
        endpoint['uri'] = self.server + clip_id
        endpoint['certificate'] = False
        http_instance = HttpRequestStandard(endpoint, payload)
        http_instance.get_request()
        result = http_instance.response.iter_content(chunk_size=1024)
        return result

    def get_image(self, clip_id):
        """
            Gets a clip from the server

        Args:
            clip_id (str): path of the clip

        Returns:
            bytes: returns the clip in mp4 format
        """
        payload = self.__prepare_http_request__()
        payload['headers']['Authorization'] = "Bearer " + self.token_auth
        endpoint = {}
        endpoint['uri'] = self.server + clip_id
        endpoint['certificate'] = False
        http_instance = HttpRequestStandard(endpoint, payload)
        http_instance.get_request()
        result = http_instance.response.content
        return result

    def get_command(self, network_id, command_id):
        """
            Gets the command result from a previous call

        Args:
            network_id (int): network of the request
            command_id (int): the ID of the command

        Returns:
            dict: json response from the server
        """
        command_id = str(command_id)
        network_id = str(network_id)
        payload = self.__prepare_http_request__()
        payload['headers']['Authorization'] = "Bearer " + self.token_auth
        endpoint = {}
        endpoint['certificate'] = False
        endpoint['uri'] = self.server + "/network/" + \
            network_id + "/command/" + command_id
        http_instance = HttpRequestStandard(endpoint, payload)
        http_instance.get_request()
        return self.__get_response_to_request__(http_instance)

    def get_video_events(self, since="2024-07-31T09%3A58%3A14%2B0000", page="1"):
        """
            Gets the list of events from the server since a date

        Args:
            since (str, optional): It will return all ocurrences from this date.
                Defaults to "2024-07-31T09%3A58%3A14%2B0000".
                page (str, optional): if it has more than one page,
                it defines de page to return. Defaults to "1".

        Returns:
            _type_: _description_
        """
        payload = self.__prepare_http_request__()
        payload['headers']['Authorization'] = "Bearer " + self.token_auth
        endpoint = {}
        endpoint['uri'] = self.server + '/api/v1/accounts/' + \
            self.account_id+'/media/changed?since='+since+'&page='+page
        endpoint['certificate'] = False
        http_instance = HttpRequestStandard(endpoint, payload)
        http_instance.get_request()
        return self.__get_response_to_request__(http_instance)

    def is_processed(self, response):
        """
        Returns if the response is processed or not

        Args:
            response (dict): JSON response from the server

        Returns:
            bool: Returns true if manifest is ready (has 'clips' key)
        """
        return bool(response and isinstance(response, dict) and 'clips' in response)

    def get_network_id_from_sync_module(self, sync_module):
        """
            Gets the network ID from the sync module
        Args:
            sync_module (int): Id of the sync module

        Returns:
            str: Id of the network
        """
        sync_modules = self.get_sync_modules()
        for sync in sync_modules:
            if sync['id'] == sync_module:
                return str(sync['network_id'])
        return ''

    def get_local_clips(self, sync_module):
        """
            Gets an array of clips from the server

        Args:
            sync_module (int): sync module id

        Returns:
            dict: array with the clips
        """
        network_id = self.get_network_id_from_sync_module(sync_module)
        request_id = self.set_sync_module_request(sync_module, network_id)
        processed = False
        payload = self.__prepare_http_request__()
        payload['headers']['Authorization'] = "Bearer " + self.token_auth
        endpoint = {}
        endpoint['certificate'] = False
        retries = MAX_RETRIES * 6  # up to 30 seconds
        while not processed and retries > 0:
            endpoint['uri'] = self.server + '/api/v1/accounts/' + \
                self.account_id+'/networks/' + str(network_id)+'/sync_modules/' + \
                str(sync_module)+'/local_storage/manifest/request/'+str(request_id)
            http_instance = HttpRequestStandard(endpoint, payload)
            http_instance.get_request()
            response = http_instance.get_json_response()
            processed = self.is_processed(response)
            retries -= 1
            if not processed:
                sleep(1)
        manifest_id = response['manifest_id']
        response = self.__get_response_to_request__(http_instance)
        response['response']['request_id'] = str(request_id)
        response['response']['network_id'] = str(network_id)
        response['response']['manifest_id'] = str(manifest_id)
        response['response']['sync_module_id'] = str(sync_module)
        return response

    def _build_clip_endpoint(self, network_id, sync_module_id, manifest_id, clip_id):
        """Build the URI for a local storage clip request."""
        return (
            f"{self.server}/api/v1/accounts/{self.account_id}"
            f"/networks/{network_id}/sync_modules/{sync_module_id}"
            f"/local_storage/manifest/{manifest_id}/clip/request/{clip_id}"
        )

    def _wait_for_command(self, command_id, network_id):
        """Poll until a sync-module command completes or timeout is reached."""
        if command_id:
            for _ in range(MAX_RETRIES * 4):
                cmd = self.get_command(str(network_id), str(command_id))
                if cmd.get('response', {}).get('complete'):
                    return
                sleep(1)
        else:
            sleep(6)

    def get_local_clip(self, clips):
        """Gets the local clip from the server.

        Args:
            clips (dict): clips dict returned by get_local_clips()

        Returns:
            iterator | dict: chunk iterator on success, error dict otherwise
        """
        if len(clips['clips']) == 0:
            return {'status_code': 404, 'is_ok': False,
                    'response': {'message': 'No clips found'}}

        network_id = clips['network_id']
        sync_module_id = clips['sync_module_id']
        manifest_id = clips['manifest_id']
        clip_id = clips['clips'][0]['id']

        payload = self.__prepare_http_request__()
        payload['headers']['Authorization'] = 'Bearer ' + self.token_auth
        endpoint = {
            'certificate': False,
            'uri': self._build_clip_endpoint(
                network_id, sync_module_id, manifest_id, clip_id
            ),
        }
        http_instance = HttpRequestStandard(endpoint, payload)
        http_instance.post_request()

        post_resp = http_instance.get_json_response()
        is_dict = isinstance(post_resp, dict)
        cmd_id = post_resp.get('id') if is_dict else None
        cmd_net = post_resp.get(
            'network_id', network_id) if is_dict else network_id
        self._wait_for_command(cmd_id, cmd_net)

        for _ in range(MAX_RETRIES):
            http_instance.get_request()
            if http_instance.response.status_code == 200:
                break
            sleep(3)

        if http_instance.response.status_code != 200:
            return self.__get_response_to_request__(http_instance)
        return http_instance.response.iter_content(chunk_size=1024)

    def set_sync_module_request(self, sync_module, network_id):
        """
           Creates a request to get the info from the sync module
        Args:
            sync_module (int): sync module id
            network_id (int): network id

        Returns:
            int: manifest request id
        """
        status_code = WAIT_CODE
        retries = MAX_RETRIES
        manifest_id = 0
        payload = self.__prepare_http_request__()
        payload['headers']['Authorization'] = "Bearer " + self.token_auth
        endpoint = {}
        endpoint['uri'] = self.server + '/api/v1/accounts/' + str(self.account_id)+'/networks/'+str(
            network_id)+'/sync_modules/' + str(sync_module)+'/local_storage/manifest/request'
        endpoint['certificate'] = False
        http_instance = HttpRequestStandard(endpoint, payload)
        while status_code == WAIT_CODE and retries > 0:
            http_instance.post_request()
            response = http_instance.get_json_response()
            retries -= 1
            status_code = http_instance.response.status_code
            if status_code == WAIT_CODE:
                sleep(1)
        if status_code != WAIT_CODE:
            manifest_id = response['id']
            return manifest_id
        return manifest_id

    def __get_newtwork_id_from_camera__(self, camera_id):
        """
            Gets the network ID from the camera ID

        Args:
            camera_id (str): is the identification of the camera
                in the blink platform. This is a int number

        Returns:
            str: returns the network ID of the camera. If it is not found,
                first, tries to get the owls and then, if everything fails,
                returns ''
        """

        cameras = self.get_cameras()
        for camera in cameras:
            if str(camera['id']) == camera_id:
                return str(camera['network_id'])
        owls = self.get_owls()
        for owl in owls:
            if str(owl['id']) == camera_id:
                return str(owl['network_id'])
        return ''

    def disarm_network(self, network_id):
        """
            Set to disarm one network

        Args:
            network_id (str): is the identification of the network
            you want to disarm

        Returns:
            list: returns the response of the server to the request
        """
        payload = self.__prepare_http_request__()
        payload['headers']['Authorization'] = "Bearer " + self.token_auth
        endpoint = {}
        endpoint['uri'] = self.server + '/api/v1/accounts/' + \
            self.account_id + '/networks/' + network_id + '/state/disarm'
        endpoint['certificate'] = False
        http_instance = HttpRequestStandard(endpoint, payload)
        http_instance.post_request()
        if http_instance.is_ok_response():
            people = int(self.config.__get_parameter__(
                "blink_number_of_people_"+str(network_id)))
            people += 1
            self.config.__set_parameter__("blink_number_of_people_"+str(network_id),
                                          str(people), "String")
        return self.__get_response_to_request__(http_instance)

    def get_login(self, re_auth=False):
        """
        OAuth2 authentication.
        - re_auth=False: full PKCE Authorization Code flow (initial login).
          Returns 412 / 2fa_required=True if Blink requires an OTP; call
          send_2fa() afterwards to complete the flow.
        - re_auth=True: silent refresh using the stored refresh_token (no 2FA).
        """
        if re_auth:
            return self.__oauth_refresh__()
        return self.__pkce_initial_login__()

    def __oauth_refresh__(self):
        """
        Silent token renewal using grant_type=refresh_token.
        Uses client_id=ios as required by the current Blink OAuth v2 server.
        """
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': _TOKEN_UA,
        }
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.config.session['REFRESH_TOKEN'],
            'client_id': _OAUTH_V2_CLIENT_ID,
            'scope': _OAUTH_SCOPE,
            'hardware_id': self.config.session['UID'],
        }
        response = _req.post(
            _OAUTH_TOKEN_URL,
            headers=headers,
            data=urlencode(data),
            verify=False,
            timeout=self.config.timeout,
        )
        json_response = json.loads(response.text)
        if 'access_token' in json_response:
            self.config.update_token_auth(json_response)
            self.token_auth = self.config.session['TOKEN_AUTH']
            self.__get_tier_info__()
        else:
            raise BlinkOAuthError(f"Token refresh failed: {json_response}")
        return {'status_code': response.status_code, 'is_ok': True, 'response': json_response}

    def __pkce_initial_login__(self):
        """
        OAuth 2.0 Authorization Code + PKCE full flow (steps 1-3).
        If Blink returns HTTP 412 (2FA required), persists the PKCE state
        (code_verifier, csrf_token, session cookies) to config storage and
        returns {'is_ok': False, 'response': {'2fa_required': True, ...}}.
        The caller must then invoke send_2fa() with the SMS code.
        If login succeeds without 2FA, immediately exchanges the code for tokens.
        """
        hardware_id = self.config.session['UID']
        code_verifier, code_challenge = _generate_pkce_pair()
        session = _req.Session()

        browser_h = {
            'User-Agent': _BROWSER_UA,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }

        # Step 1: Authorization request — sets session cookies on the OAuth server
        params = {
            'app_brand': 'blink',
            'app_version': '50.1',
            'client_id': _OAUTH_V2_CLIENT_ID,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
            'device_brand': 'Apple',
            'device_model': 'iPhone16,1',
            'device_os_version': '26.1',
            'hardware_id': hardware_id,
            'redirect_uri': _OAUTH_REDIRECT_URI,
            'response_type': 'code',
            'scope': _OAUTH_SCOPE,
        }
        session.get(
            _OAUTH_V2_AUTHORIZE, params=params, headers=browser_h,
            verify=False, timeout=self.config.timeout,
        )

        # Step 2: Signin page → extract CSRF token
        signin_page = session.get(
            _OAUTH_V2_SIGNIN, headers=browser_h,
            verify=False, timeout=self.config.timeout,
        )
        csrf_token = _extract_csrf(signin_page.text)
        if not csrf_token:
            raise BlinkLoginError(
                'Failed to extract CSRF token from Blink signin page')

        # Step 3: Submit credentials
        cred_h = {
            'User-Agent': _BROWSER_UA,
            'Accept': '*/*',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': _OAUTH_BASE,
            'Referer': _OAUTH_V2_SIGNIN,
        }
        signin = session.post(
            _OAUTH_V2_SIGNIN,
            headers=cred_h,
            data={
                'username': self.config.auth['USER'],
                'password': self.config.auth['PASSWORD'],
                'csrf-token': csrf_token,
            },
            allow_redirects=False,
            verify=False,
            timeout=self.config.timeout,
        )

        if signin.status_code == 412:
            # 2FA required — save state so send_2fa() can complete the flow
            cookies = dict(session.cookies)
            self.config.save_oauth_state(code_verifier, csrf_token, cookies)
            return {
                'status_code': 412,
                'is_ok': False,
                'response': {
                    '2fa_required': True,
                    'message': '2FA code required. Send the SMS code to /send_2fa.',
                },
            }
        if signin.status_code in (301, 302, 303, 307, 308):
            # Direct success (no 2FA configured on this account)
            return self.__pkce_exchange_code__(session, code_verifier, hardware_id)

        raise BlinkLoginError(
            f'PKCE signin failed: HTTP {signin.status_code} — {signin.text}')

    def __pkce_exchange_code__(self, session, code_verifier, hardware_id=None):
        """
        Steps 4-5 of PKCE flow: retrieve the authorization code from the
        redirect URL and exchange it for an access_token + refresh_token.
        """
        if hardware_id is None:
            hardware_id = self.config.session['UID']

        browser_h = {
            'User-Agent': _BROWSER_UA,
            'Accept': '*/*',
            'Referer': _OAUTH_V2_SIGNIN,
        }

        # Step 4: Follow the authorize redirect to extract the auth code
        auth_resp = session.get(
            _OAUTH_V2_AUTHORIZE, headers=browser_h,
            allow_redirects=False, verify=False, timeout=self.config.timeout,
        )
        location = auth_resp.headers.get('Location', '')
        code = parse_qs(urlparse(location).query).get('code', [None])[0]
        if not code:
            raise BlinkOAuthError(
                f'Failed to get authorization code. Redirect: {location}')

        # Step 5: Exchange code for tokens
        token_h = {
            'User-Agent': _TOKEN_UA,
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': '*/*',
        }
        token_data = {
            'app_brand': 'blink',
            'client_id': _OAUTH_V2_CLIENT_ID,
            'code': code,
            'code_verifier': code_verifier,
            'grant_type': 'authorization_code',
            'hardware_id': hardware_id,
            'redirect_uri': _OAUTH_REDIRECT_URI,
            'scope': _OAUTH_SCOPE,
        }
        token_resp = _req.post(
            _OAUTH_TOKEN_URL,
            headers=token_h,
            data=urlencode(token_data),
            verify=False,
            timeout=self.config.timeout,
        )
        json_response = json.loads(token_resp.text)
        if 'access_token' in json_response:
            self.config.update_token_auth(json_response)
            self.token_auth = self.config.session['TOKEN_AUTH']
            self.__get_tier_info__()
        else:
            raise BlinkOAuthError(f'Token exchange failed: {json_response}')
        return {'status_code': token_resp.status_code, 'is_ok': True, 'response': json_response}

    def send_2fa(self, pin):
        """
        Complete the PKCE 2FA flow.
        Loads the PKCE state (code_verifier, csrf_token, cookies) saved by
        __pkce_initial_login__(), verifies the SMS code, then exchanges the
        resulting authorization code for an access_token + refresh_token.

        Args:
            pin (int | str): OTP received by SMS.

        Returns:
            dict: standard {'status_code', 'is_ok', 'response'} result.
        """
        state = self.config.load_oauth_state()
        code_verifier = state['code_verifier']
        csrf_token = state['csrf_token']
        hardware_id = self.config.session['UID']

        session = _req.Session()
        for name, value in state.get('cookies', {}).items():
            session.cookies.set(name, value)

        # Step 3b: Verify the SMS OTP
        twofa_h = {
            'User-Agent': _BROWSER_UA,
            'Accept': '*/*',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': _OAUTH_BASE,
            'Referer': _OAUTH_V2_SIGNIN,
        }
        verify = session.post(
            _OAUTH_V2_2FA_VERIFY,
            headers=twofa_h,
            data={'2fa_code': str(
                pin), 'csrf-token': csrf_token, 'remember_me': 'false'},
            verify=False,
            timeout=self.config.timeout,
        )
        if verify.status_code != 201:
            return {
                'status_code': verify.status_code,
                'is_ok': False,
                'response': {'message': f'2FA verification failed: {verify.text}'},
            }
        try:
            result = json.loads(verify.text)
            if result.get('status') != 'auth-completed':
                return {'status_code': verify.status_code, 'is_ok': False, 'response': result}
        except json.JSONDecodeError:
            pass

        # Steps 4-5: Exchange code for tokens
        return self.__pkce_exchange_code__(session, code_verifier, hardware_id)

    def get_networks(self):
        """
            Using basic info, gets the networks of the account

        Returns:
            list: list of networks in the account
        """
        result = self.get_home_screen_info()
        response = result['response']['networks']
        return response

    def get_owls(self):
        """
            Using basic info, gets the owls of the account

        Returns:
            list: list of owls in the account
        """
        result = self.get_home_screen_info()
        response = result['response']['owls']
        return response

    def get_sync_modules(self):
        """
            Using basic info, gets the sync_modules of the account

        Returns:
            list: list of sync_modules  in the account
        """
        result = self.get_home_screen_info()
        response = result['response']['sync_modules']
        return response

    def get_cameras(self):
        """
            Using basic info, gets the cameras of the account

        Returns:
            list: list of cameras  in the account
        """
        result = self.get_home_screen_info()
        response = result['response']['cameras']
        return response

    def get_home_screen_info(self):
        """
            Gets the home screen info of the account

        Returns:
            dict : This responses a json with the status_code,
            the response of the server(blank if has no json format) and if is_success
        """
        payload = self.__prepare_http_request__()
        payload['headers']['Authorization'] = "Bearer " + self.token_auth
        endpoint = {}
        endpoint['uri'] = self.server + '/api/v3/accounts/' + \
            self.account_id + '/homescreen'
        endpoint['certificate'] = False
        http_instance = HttpRequestStandard(endpoint, payload)
        http_instance.get_request()
        return self.__get_response_to_request__(http_instance)

    def __get_tier_info__(self):
        """
        Calls the Blink tier endpoint to get the account_id and region server.
        Must be called after a successful login/token refresh.
        Updates self.account_id, self.server and the config session values.
        """
        payload = self.__prepare_http_request__()
        payload['headers']['Authorization'] = "Bearer " + self.token_auth
        endpoint = {
            'uri': _TIER_URL,
            'certificate': False
        }
        http_instance = HttpRequestStandard(endpoint, payload)
        http_instance.get_request()
        json_response = json.loads(http_instance.response.text)
        tier = json_response.get('tier')
        account_id = str(json_response.get('account_id', self.account_id))
        if tier:
            self.set_tier(tier)
            self.get_server()
        if account_id:
            self.set_account_id(account_id)
        self.config.update_tier_info(tier, account_id)
        return json_response

    def set_thumbnail(self, camera_id):
        """
            Set the thumbnail of a camera

        Args:
            camera_id (str): Id of the camera you want to update the thumbnail

        Returns:
            dict : This responses a json with the status_code,
            the response of the server(blank if has no json format) and if is_success
        """
        network_id = self.__get_newtwork_id_from_camera__(camera_id)
        payload = self.__prepare_http_request__()
        payload['headers']['Authorization'] = "Bearer " + self.token_auth
        endpoint = {}
        endpoint['uri'] = self.server + '/network/' + \
            network_id + '/camera/' + camera_id + '/thumbnail'
        endpoint['certificate'] = False
        http_instance = HttpRequestStandard(endpoint, payload)
        status_code = WAIT_CODE
        retries = MAX_RETRIES
        while status_code == WAIT_CODE and retries > 0:
            http_instance.post_request()
            status_code = http_instance.response.status_code
            retries -= 1
            if status_code == WAIT_CODE:
                sleep(1)
        return self.__get_response_to_request__(http_instance)

    def set_owl_thumbnail(self, owl_id):
        """
            Set the thumbnail of a Owl

        Args:
            owl_id (str): Id of the owl you want to update the thumbnail

        Returns:
            dict : This responses a json with the status_code,
            the response of the server(blank if has no json format) and if is_success
        """
        network_id = self.__get_newtwork_id_from_camera__(owl_id)
        payload = self.__prepare_http_request__()
        payload['headers']['Authorization'] = "Bearer " + self.token_auth
        endpoint = {}
        endpoint['uri'] = self.server + '/api/v1/accounts/'+self.account_id + \
            '/networks/' + network_id + '/owls/' + owl_id + '/thumbnail'
        endpoint['certificate'] = False
        http_instance = HttpRequestStandard(endpoint, payload)
        status_code = WAIT_CODE
        retries = MAX_RETRIES
        while status_code == WAIT_CODE and retries > 0:
            http_instance.post_request()
            status_code = http_instance.response.status_code
            retries -= 1
            if status_code == WAIT_CODE:
                sleep(1)
        return self.__get_response_to_request__(http_instance)
