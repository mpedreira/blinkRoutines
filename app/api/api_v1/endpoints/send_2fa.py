"""
    This module is responsible for completing the Blink PKCE 2FA flow.
"""
# pylint: disable=E0401,R0903

from fastapi import APIRouter
from app.classes.adapters.blink_api import BlinkAPI
from app.classes.adapters.config_aws import ConfigAWS


router = APIRouter()


@router.post("/")
def send_2fa(mfa_code: int):
    """
        Completes the Blink PKCE 2FA flow started by /get_basic_config.
        Reads the PKCE state (code_verifier, csrf_token, cookies) that was
        persisted during the login step, verifies the SMS OTP with Blink,
        and exchanges the resulting authorization code for tokens.

    Args:
        mfa_code (int): SMS OTP received on the registered phone number.

    Returns:
        dict : {'TOKEN_AUTH', 'TIER', 'ACCOUNT_ID'} on success,
               or {'is_ok': False, 'message': ...} on failure.
    """
    config_instance = ConfigAWS()
    blink_instance = BlinkAPI(config_instance)
    result = blink_instance.send_2fa(mfa_code)
    if not result['is_ok']:
        return result['response']
    response = {}
    response['TOKEN_AUTH'] = result['response'].get('access_token', '')
    response['TIER'] = config_instance.session.get('TIER', '')
    response['ACCOUNT_ID'] = config_instance.session.get('ACCOUNT_ID', '')
    response['CLIENT_ID'] = config_instance.session.get('CLIENT_ID', '')
    return response
