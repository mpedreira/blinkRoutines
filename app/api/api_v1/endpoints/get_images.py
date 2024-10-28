"""
This file contains the endpoint to arm a network.
"""
# pylint: disable=E0401,R0801

from fastapi import APIRouter
from app.classes.adapters.blink_api import BlinkAPI
from app.classes.adapters.config_aws import ConfigAWS
from app.classes.adapters.telegram_api import TelegramApi

CAM_ID = {"Entrada": {"id": '566211', "type": "cam"}, "Finca1": {"id": "791888", "type": "cam"}, "Finca2": {"id": "848119", "type": "cam"},
          "Coruna": {"id": '1217831', "type": "cam"}, "Finca3": {"id": "1220146", "type": "cam"}, "Mateo": {"id": "586118", "type": "owl"}}


router = APIRouter()
""" This creates the new API path /arm/{newtork_id} """


@router.get("/{channel}/{cam_name}")
def get_images(channel: str, cam_name: str):
    """
        Function that calls the BlinkAPI class to arm a network.

    Args:
        network_id (int): ID of the network you want to arm

    Returns:
        dict : This responses a json with the status_code, 
        the response of the server(blank if has no json format) and if is_success
    """
    config_instance = ConfigAWS()
    blink_instance = BlinkAPI(config_instance)
    telegram_instance = TelegramApi(config_instance)
    if is_cam(cam_name):
        thumb = get_camera_thumb(cam_name, blink_instance)
    else:
        thumb = get_own_thumb(cam_name, blink_instance)

    response = blink_instance.get_clip(thumb)
    image_clip = b''.join(chunk for chunk in response if chunk)
    response = telegram_instance.send_image_from_bytes(image_clip, channel)
    return response


def get_own_thumb(cam_name, blink_instance):
    owl_id = CAM_ID[cam_name]["id"]
    response = blink_instance.set_owl_thumbnail(owl_id)
    response = blink_instance.get_home_screen_info()
    for owl in response['response']['cameras']:
        if owl['id'] == int(owl_id):
            url = owl['thumbnail']
    return url


def get_camera_thumb(cam_name, blink_instance):
    cam_id = CAM_ID[cam_name]["id"]
    response = blink_instance.set_thumbnail(cam_id)
    response = blink_instance.get_home_screen_info()
    for camera in response['response']['cameras']:
        if camera['id'] == int(cam_id):
            url = camera['thumbnail']
    return url


def is_cam(cam_name):
    return CAM_ID[cam_name]["type"] == "cam"
