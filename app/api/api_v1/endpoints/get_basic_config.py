"""
This file contains the FastAPI endpoint for getting the basic configuration of the Blink API.
This info is required for config rest of the modules
"""
# pylint: disable=E0401,R0903

from fastapi import APIRouter
from pydantic import BaseModel
from app.classes.adapters.blink_api import BlinkAPI
from app.classes.adapters.config_aws import ConfigAWS


class User(BaseModel):
    """
        Information required for the user to login to the Blink API.
    """
    username: str
    password: str


router = APIRouter()
""" This creates the new API path /get_basic_config """


@router.post("/")
def get_config(user: User):
    """
        Function that calls the BlinkAPI class to get the basic configuration of the Blink API.

    Args:
        user (User): information of user and password required for 
                    retrieving the basic configuration

    Returns:
        dict : This responses a json with the status_code, 
            the response of the server(blank if has no json format) and if is_success
    """
    config_instance = ConfigAWS()
    config_instance.auth = {}
    config_instance.auth['USER'] = user['username']
    config_instance.auth['PASSWORD'] = user['password']
    blink_instance = BlinkAPI(config_instance)
    login = blink_instance.get_login()
    response = {}
    response['tier'] = login['response']['account']['tier']
    response['ACCOUNT_ID'] = login['response']['account']['account_id']
    response['CLIENT_ID'] = login['response']['account']['client_id']
    response['TOKEN_AUTH'] = login['response']['account']['auth']['token']
    return response
