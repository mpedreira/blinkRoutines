#!/usr/bin/env python3
# pylint: disable=I1101,E0401,R0801
"""Module for HTTP standard connection"""
import requests
from app.classes.http_request import HttpRequest


STATUS_CODE = {'OK': {201, 200, 204}, 'ERROR': {401, 400, 500, 404}}


class HttpRequestStandard(HttpRequest):
    """Module for HTTP standard connection"""

    def delete_request(self):
        """Delete call with standard configuration"""
        try:
            self.response = requests.delete(
                self.endpoint['uri'],
                auth=self.payload['auth'],
                data=self.payload['data'],
                headers=self.payload['headers'],
                verify=self.endpoint['certificate'],
                timeout=self.payload['timeout']
            )
        except requests.exceptions.SSLError:
            pass
        self.response.close()
        return self.is_ok_response()

    def get_request(self):
        """Get call with standard configuration"""
        try:
            self.response = requests.get(
                self.endpoint['uri'],
                auth=self.payload['auth'],
                verify=self.endpoint['certificate'],
                headers=self.payload['headers'],
                timeout=self.payload['timeout']
            )
        except requests.exceptions.SSLError:
            pass
        self.response.close()
        return self.is_ok_response()

    def patch_request(self):
        """Patch call with standard configuration"""
        try:
            self.response = requests.patch(
                self.endpoint['uri'],
                data=self.payload['data'],
                headers=self.payload['headers'],
                auth=self.payload['auth'],
                verify=self.endpoint['certificate'],
                timeout=self.payload['timeout']
            )
        except requests.exceptions.SSLError:
            pass
        self.response.close()
        return self.is_ok_response()

    def post_request(self):
        """Post call with standard configuration"""
        try:
            self.response = requests.post(
                self.endpoint['uri'],
                data=self.payload['data'],
                headers=self.payload['headers'],
                auth=self.payload['auth'],
                verify=self.endpoint['certificate'],
                timeout=self.payload['timeout']
            )
        except requests.exceptions.SSLError:
            pass
        return self.is_ok_response()

    def put_request(self):
        """Put call with standard configuration"""
        try:
            self.response = requests.put(
                self.endpoint['uri'],
                auth=self.payload['auth'],
                data=self.payload['data'],
                headers=self.payload['headers'],
                verify=self.endpoint['certificate'],
                timeout=self.payload['timeout']
            )
        except requests.exceptions.SSLError:
            pass
        self.response.close()
        return self.is_ok_response()
