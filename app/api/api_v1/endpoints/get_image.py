"""
This file contains the endpoint to get the images from the cameras in telegram
"""
# pylint: disable=E0401,R0801,E0611

from datetime import datetime
from time import sleep
from fastapi import APIRouter
from app.classes.adapters.blink_api import BlinkAPI
from app.classes.adapters.config_aws import ConfigAWS
from app.classes.adapters.telegram_api import TelegramApi

CAM_ID = {}
EMPTY = ""

router = APIRouter()
""" This creates the new API path /arm/{newtork_id} """


@router.get("/{channel_id}/{cam_name}")
def get_image(channel_id: str, cam_name: str):
    """
        Function that calls the BlinkAPI class, gets the thumb and send it to the telegram channel

    Args:
        channel_id (str): ID of the telegram channel
        cam_name (str): Name of the camera to get the thumb

    Returns:
        dict : This responses a json with the status_code, 
        the response of the server(blank if has no json format) and if is_success
    """
    config_instance = ConfigAWS()
    telegram_instance = TelegramApi(config_instance)
    cam_array = config_instance.cameras
    blink_instance = BlinkAPI(config_instance)
    blink_instance.__set_token__()
    blink_instance.get_server()
    camera_id = cam_array[cam_name]['id']
    cam_type = cam_array[cam_name]['type']
    if is_camera(cam_type):
        path = get_camara_thumb(blink_instance, camera_id)
    else:
        path = get_own_thumb(blink_instance, camera_id)
    thumb = blink_instance.get_image(path)
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = "Enviando imagen de " + cam_name + " a las " + date
    response = telegram_instance.send_message(message, channel_id)
    response = telegram_instance.send_image_from_bytes(thumb, channel_id)

    return response


def get_own_thumb(blink_instance, camera_id):
    """
        Get the thumb of the owl
    Args:
        blink_instance (class): Class of the blink api
        camera_id (str): id of the camera

    Returns:
        str: Path of the thumb
    """
    blink_instance.set_owl_thumbnail(camera_id)
    sleep(5)
    response = blink_instance.get_home_screen_info()
    for owl in response['response']['owl']:
        if owl['id'] == int(camera_id):
            return owl['thumbnail']
    return EMPTY


def get_camara_thumb(blink_instance, camera_id):
    """
        Get the thumb of the camera
    Args:
        blink_instance (class): Class of the blink api
        camera_id (str): id of the camera

    Returns:
        str: Path of the thumb
    """
    blink_instance.set_thumbnail(camera_id)
    sleep(5)
    response = blink_instance.get_home_screen_info()
    for camera in response['response']['cameras']:
        if camera['id'] == int(camera_id):
            return camera['thumbnail']
    return EMPTY


def is_camera(cam_type):
    """
        Decides if the camera is a camera or a owl

    Args:
        cam_type (str): type of the camera

    Returns:
        bool: True if it is a cam, False if it is a owl
    """
    if cam_type == "cam":
        return True
    return False
