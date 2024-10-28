#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Module for using Blink Cameras through API"""

import json
from app.classes.blink import Blink
from app.classes.adapters.http_request_standard import HttpRequestStandard


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
        self.set_token_auth(self.config.session['TOKEN_AUTH'])
        self.set_client_id(self.config.session['CLIENT_ID'])

    def __get_basics__(self):
        """
            Gets the basic information of the blink account
        """
        response = self.get_login()
        self.basic_info = response['response']
        self.get_server()
        self.get_client_id()
        self.get_account_id()

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
        payload['headers']['token-auth'] = self.token_auth
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
        payload['headers']['token-auth'] = self.token_auth
        endpoint = {}
        endpoint['uri'] = self.server + clip_id
        endpoint['certificate'] = False
        http_instance = HttpRequestStandard(endpoint, payload)
        http_instance.get_request()
        result = http_instance.response.iter_content(chunk_size=1024)
        return result

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
        payload['headers']['token-auth'] = self.token_auth
        endpoint = {}
        endpoint['uri'] = self.server + '/api/v1/accounts/' + \
            self.account_id+'/media/changed?since='+since+'&page='+page
        endpoint['certificate'] = False
        http_instance = HttpRequestStandard(endpoint, payload)
        http_instance.get_request()
        return self.__get_response_to_request__(http_instance)

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

    def get_camera_clip(self, camera_id):
        """_summary_

        Args:
            network_id (_type_): _description_
            camera_id (_type_): _description_

        Returns:
            _type_: _description_
        """
        network_id = self.__get_newtwork_id_from_camera__(camera_id)
        payload = self.__prepare_http_request__()
        payload['headers']['token-auth'] = self.token_auth
        endpoint = {}
        endpoint['uri'] = self.server + '/network/' + \
            network_id + '/camera/' + camera_id + '/clip'
        endpoint['certificate'] = False
        http_instance = HttpRequestStandard(endpoint, payload)
        http_instance.post_request()
        return self.__get_response_to_request__(http_instance)

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
        payload['headers']['token-auth'] = self.token_auth
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
            Login in the server

        Returns:
            list: return the response of the server for the login
                this info is used for generat basic info
        """
        payload = self.__prepare_http_request__()
        endpoint = {}
        endpoint['uri'] = self.server + '/api/v5/account/login'
        endpoint['certificate'] = False
        data = {}
        data['password'] = self.config.auth['PASSWORD']
        data['email'] = self.config.auth['USER']
        data['unique_id'] = self.config.session['UID']
        if re_auth:
            self.get_server()
            data['reauth'] = 'true'
        payload['data'] = json.dumps(data)
        http_instance = HttpRequestStandard(endpoint, payload)
        http_instance.post_request()
        if re_auth:
            json_response = json.loads(http_instance.response.text)
            self.config.update_token_auth(json_response)
        return self.__get_response_to_request__(http_instance)

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
        payload['headers']['token-auth'] = self.token_auth
        endpoint = {}
        endpoint['uri'] = self.server + 'api/v3/accounts/' + \
            self.account_id + '/homescreen'
        endpoint['certificate'] = False
        http_instance = HttpRequestStandard(endpoint, payload)
        http_instance.get_request()
        return self.__get_response_to_request__(http_instance)

    def __update_token__(self):
        """
            Updates the token of the class
        """
        response = self.get_login(True)
        self.config.update_token_auth(response['response'])
        self.token_auth = self.config.session['TOKEN_AUTH']

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
        payload['headers']['token-auth'] = self.token_auth
        endpoint = {}
        endpoint['uri'] = self.server + '/network/' + \
            network_id + '/camera/' + camera_id + '/thumbnail'
        endpoint['certificate'] = False
        http_instance = HttpRequestStandard(endpoint, payload)
        http_instance.post_request()
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
        payload['headers']['token-auth'] = self.token_auth
        endpoint = {}
        endpoint['uri'] = self.server + 'api/v1/accounts/'+self.account_id + \
            '/networks/' + network_id + '/owls/' + owl_id + '/thumbnail'
        endpoint['certificate'] = False
        http_instance = HttpRequestStandard(endpoint, payload)
        http_instance.post_request()
        return self.__get_response_to_request__(http_instance)

    def send_2fa(self, pin):
        """
            Send the 2FA pin to the server

        Args:
            pin (int): mfa recieved in the phone

        Returns:
            dict : This responses a json with the status_code,
            the response of the server(blank if has no json format) and if is_success
        """
        payload = self.__prepare_http_request__()
        payload['headers']['token-auth'] = self.token_auth
        endpoint = {}
        endpoint['uri'] = self.server + 'api/v4/account/' + \
            self.account_id + '/client/'+self.client_id+'/pin/verify'
        endpoint['certificate'] = False
        data = {}
        data['pin'] = pin
        data['unique_id'] = self.unique_id
        payload['data'] = json.dumps(data)
        http_instance = HttpRequestStandard(endpoint, payload)
        http_instance.post_request()
        return self.__get_response_to_request__(http_instance)
