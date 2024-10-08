#!/usr/bin/env python3
"""Class for HTTP request"""
# pylint: disable=E1101,I1101,E0401
import json
import urllib3

STATUS_CODE = {'OK': {201, 200, 204}, 'ERROR': {401, 400, 500, 404}}


class HttpRequest:
    """ Intending of following Hexagonal Architecture, this class is the core for HTTP request"""

    def __init__(self, endpoint, payload):
        """Data inicialization of HTTP module. 
        This is the basic information you need for a HTTP request"""
        self.endpoint = {}
        self.payload = {}
        self.endpoint['uri'] = endpoint['uri']
        self.payload['auth'] = payload['auth']
        self.endpoint['certificate'] = endpoint['certificate']
        self.payload['headers'] = payload['headers']
        self.payload['data'] = payload['data']
        self.payload['timeout'] = payload['timeout']
        self.payload['files'] = ''
        if 'files' in payload.keys():
            self.payload['files'] = payload['files']
        self.response = ''
        urllib3.disable_warnings()

    def update_data(self, endpoint, payload):
        """ This module update the basic configuration defined in __init__

        Args:
            endpoint (list): 
                    JSON with the info you want to do the request. 
                    At least, you need the uri and the certificate
            payload (list): 
                    JSON with the info you want to do the payload. 
                    At least, you need the auth, headers, data and timeout
        """
        self.endpoint = {}
        self.payload = {}
        self.endpoint['uri'] = endpoint['uri']
        self.payload['auth'] = payload['auth']
        self.endpoint['certificate'] = endpoint['certificate']
        self.payload['headers'] = payload['headers']
        self.payload['data'] = payload['data']
        self.payload['timeout'] = payload['timeout']
        if 'files' in payload.keys():
            self.payload['files'] = payload['files']
        self.payload['files'] = payload['files']

    def get_json_response(self):
        """Formats the response in JSON

        Returns:
            list: json_response of the request
        """
        json_response = json.loads(self.response.text)
        return json_response

    def is_ok_response(self):
        """Validates the response code of the request

        Returns:
            bool: Returns true if the STATUS_CODE is in OK or false if not
        """
        try:
            if self.get_status_code() in STATUS_CODE['OK']:
                return True
            return False
        except AttributeError:
            return False

    def get_status_code(self):
        """Returns the status code of the request

        Returns:
            int: Returns the status code of the request
        """
        return self.response.status_code

    def delete_request(self):
        """Do the request with DELETE method. This should be rewritten in kids"""
        return True

    def get_request(self):
        """Do the request with GET method. This should be rewritten in kids"""
        return True

    def patch_request(self):
        """Do the request with PATH method. This should be rewritten in kids"""
        return True

    def post_request(self):
        """Do the request with POST method. This should be rewritten in kids"""
        return True

    def put_request(self):
        """Do the request with PUT method. This should be rewritten in kids"""
        return True
