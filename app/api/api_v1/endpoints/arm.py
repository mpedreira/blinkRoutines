"""
This file contains the endpoint to arm a network.
"""
# pylint: disable=E0401

from fastapi import APIRouter
from app.classes.adapters.blink_api import BlinkAPI
from app.classes.adapters.config_static import ConfigStatic

router = APIRouter()
""" This creates the new API path /arm/{newtork_id} """


@router.get("/{newtork_id}")
def arm(newtork_id: int):
    """
        Function that calls the BlinkAPI class to arm a network.

    Args:
        network_id (int): ID of the network you want to arm

    Returns:
        dict : This responses a json with the status_code, 
        the response of the server(blank if has no json format) and if is_success
    """
    config_instance = ConfigStatic()
    blink_instance = BlinkAPI(config_instance)
    blink_instance.__set_token__()
    blink_instance.get_server()
    return {"item_id": blink_instance.arm_network(str(newtork_id))}
