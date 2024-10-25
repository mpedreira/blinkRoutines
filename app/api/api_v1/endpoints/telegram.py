"""
    This module is responsible for sending the 2FA code to the Blink API.
"""
# pylint: disable=E0401,R0903

from fastapi import APIRouter
from app.classes.adapters.telegram_api import TelegramApi
from app.classes.adapters.config_aws import ConfigAWS


router = APIRouter()


@router.get("/{channel_id}")
def send_message(channel_id: str, message: str):
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
    telegram_instance = TelegramApi(config_instance)
    response = telegram_instance.send_message(message, channel_id)
    return response
