"""
    This module is responsible for sending the 2FA code to the Blink API.
"""
# pylint: disable=E0401,R0903

from fastapi import APIRouter
from pydantic import BaseModel
from app.classes.adapters.blink_api import BlinkAPI
from app.classes.adapters.config_aws import ConfigAWS


class Account(BaseModel):
    """
        Class that represents the info required from the account for validating 2FA
    """
    tier: str
    account_id: int
    client_id: int
    token_auth: str


router = APIRouter()


@router.post("/")
def send_2fa(account: Account, mfa_code: int):
    """
        Function that calls the BlinkAPI class to send the 2FA code to the Blink API.

    Args:
        account (Account): all information required for validating a client
        mfa_code (int): this is the sms that you will receive in your phone

    Returns:
        dict : This responses a json with the status_code, 
        the response of the server(blank if has no json format) and if is_success
    """
    config_instance = ConfigAWS()
    config_instance.auth = {}
    blink_instance = BlinkAPI(config_instance)
    blink_instance.set_tier(account['tier'])
    blink_instance.set_account_id(str(account['account_id']))
    blink_instance.set_client_id(str(account['client_id']))
    blink_instance.set_token_auth(account['token_auth'])
    blink_instance.get_server()
    response = blink_instance.send_2fa(mfa_code)
    return response
