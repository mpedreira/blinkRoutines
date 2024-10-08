"""
This file contains the endpoint to disarm a network.
"""
# pylint: disable=E0401,R0801

from fastapi import APIRouter
from app.classes.adapters.blink_api import BlinkAPI
from app.classes.adapters.config_static import ConfigStatic

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
    config_instance = ConfigStatic()
    blink_instance = BlinkAPI(config_instance)
    blink_instance.__set_token__()
    blink_instance.get_server()
    return blink_instance.disarm_network(str(network_id))
