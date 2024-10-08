""" This module contains the endpoint for updating the thumbnail of an owl. """
# pylint: disable=E0401,R0801

from fastapi import APIRouter
from app.classes.adapters.blink_api import BlinkAPI
from app.classes.adapters.config_aws import ConfigAWS

router = APIRouter()
""" This creates the new API path /update_thumb/{owl_id} """


@router.get("/{owl_id}")
def update_owl_thumb(owl_id: int):
    """
        This API call updates the thumbnail of an owl.
    Args:
        owl_id (int): id of the owl you want to update the thumbnail

    Returns:
        dict : This responses a json with the status_code, 
        the response of the server(blank if has no json format) and if is_success
    """
    config_instance = ConfigAWS()
    blink_instance = BlinkAPI(config_instance)
    blink_instance.__set_token__()
    blink_instance.get_server()
    return blink_instance.set_owl_thumbnail(str(owl_id))
