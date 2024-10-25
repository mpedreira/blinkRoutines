"""
Tests ConfigMock
"""
# pylint: disable=C0301,C0303,C0103,E0401,E0611
import random
import string
import json
from app.classes.adapters.config_static import ConfigStatic


def test_get_claroty_config():
    """
    Tests get_claroty_config
    """
    config_instance = ConfigStatic()

    assert config_instance.endpoints['BLINK'] == "https://rest-prod.immedia-semi.com/"


def test_update_token_auth():
    token = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    response = {}
    response['auth'] = {}
    response['auth']['token'] = token
    config_instance = ConfigStatic()
    config_instance.update_token_auth(response)
    assert config_instance.session['TOKEN_AUTH'] == token
