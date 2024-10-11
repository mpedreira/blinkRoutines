"""
This file contains the endpoint to disarm a network.
"""
# pylint: disable=E0401,R0801

from fastapi import APIRouter
from app.classes.adapters.blink_api import BlinkAPI
from app.classes.adapters.config_aws import ConfigAWS

router = APIRouter()
""" This creates the new API path /disarm/{network_id} """


@router.get("/{network_id}")
def disarm(network_id: int):
    """
        Function that calls the BlinkAPI class to disarm a network.

    Args:
        network_id (int): ID of the network you want to disarm

    Returns:
        dict : This responses a json with the status_code, 
        the response of the server(blank if has no json format) and if is_success
    """
    config_instance = ConfigAWS()
    blink_instance = BlinkAPI(config_instance)
    response = disarm_network(blink_instance, network_id)
    if need_retry(response):
        retry = True
        response = disarm_network(blink_instance, network_id, retry)
    return response


def disarm_network(blink_instance, network_id, retry=False):
    """
        Commands that you may do if you want to disarm your 
        Blink Camera
    Args:
        blink_instance (Class): An instance of Blink
        network_id (int): ID of the network you want to disarm
        retry (bool, optional): Defines if it is a first attent to login or not.
                If is not the first attent, you need to update your token 
                Defaults to False.

    Returns:
        dict : This responses a json with the status_code,
            the response of the server(blank if has no json format) and if is_success
    """
    if retry:
        blink_instance.__update_token__()
    blink_instance.__set_token__()
    blink_instance.get_server()
    return blink_instance.disarm_network(str(network_id))


def need_retry(response):
    """
        Defines if it is needet to reautenticate

    Args:
        response (String): Response of the server

    Returns:
        bol: returns True if the response is not ok 
            and False if it is ok
    """
    return not response['is_ok']
