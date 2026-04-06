"""
This file contains the FastAPI endpoint for getting the basic configuration of the Blink API.
This info is required for config rest of the modules
"""
# pylint: disable=E0401,R0903

from fastapi import APIRouter
from pydantic import BaseModel
from app.classes.adapters.blink_api import BlinkAPI
from app.classes.adapters.config_aws import ConfigAWS


router = APIRouter()
""" This creates the new API path /get_basic_config """


class LoginRequest(BaseModel):
    """Request body for the login endpoint."""
    username: str
    password: str


@router.post("/")
def get_config(body: LoginRequest):
    """
        Initiates the Blink OAuth 2.0 PKCE login flow.

        If Blink requires 2FA, returns {'2fa_required': True, 'message': ...}.
        The client should then POST the SMS code to /send_2fa.

        On success (no 2FA), returns {'TOKEN_AUTH': '<token>', ...}.

    Args:
        body (LoginRequest): Blink account email and password in the request body

    Returns:
        dict : login result
    """
    config_instance = ConfigAWS()
    config_instance.auth = {}
    config_instance.auth['USER'] = body.username
    config_instance.auth['PASSWORD'] = body.password
    blink_instance = BlinkAPI(config_instance)
    login = blink_instance.get_login()
    if not login['is_ok']:
        # 2FA required — return the server message so the client knows to call /send_2fa
        return login['response']
    response = {}
    response['TOKEN_AUTH'] = login['response'].get('access_token', '')
    response['TIER'] = config_instance.session.get('TIER', '')
    response['ACCOUNT_ID'] = config_instance.session.get('ACCOUNT_ID', '')
    return response
