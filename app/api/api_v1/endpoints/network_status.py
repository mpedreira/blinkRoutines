"""Endpoint to read whether a Blink network is enabled (armed) or not."""
# pylint: disable=E0401

from fastapi import APIRouter
from app.classes.adapters.blink_api import BlinkAPI
from app.classes.adapters.config_aws import ConfigAWS


router = APIRouter()


@router.get("/{network_id}")
def network_status(network_id: int):
    """Return the armed/enabled state for a network."""
    config_instance = ConfigAWS()
    blink_instance = BlinkAPI(config_instance)
    blink_instance.__set_token__()
    blink_instance.get_server()
    return blink_instance.get_network_status(str(network_id))