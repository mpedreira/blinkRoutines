""" This module creates the API path /update_thumb/{camera} """
# pylint: disable=E0401,R0801

from fastapi import APIRouter
from app.classes.adapters.blink_api import BlinkAPI
from app.classes.adapters.config_aws import ConfigAWS

router = APIRouter()
""" This creates the new API path /update_thumb/{camera} """


@router.get("/{camera}")
def update_thumb(camera: int):
    """
        This API call updates the thumbnail of a camera.
    Args:
        camera_id (int): id of the camera you want to update the thumbnail

    Returns:
        dict : This responses a json with the status_code, 
        the response of the server(blank if has no json format) and if is_success
    """
    # raise Exception('This is a test exception.')
    config_instance = ConfigAWS()
    blink_instance = BlinkAPI(config_instance)
    blink_instance.__set_token__()
    blink_instance.get_server()
    # print(blink_instance.get_cameras())
    # print(blink_instance.get_video_events())
    # print(blink_instance.get_cameras())
    return {"item_id": blink_instance.set_thumbnail(str(camera))}
