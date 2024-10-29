"""
This file contains the endpoint to get the images from the cameras in telegram
"""
# pylint: disable=E0401,R0801,E0611

from datetime import datetime, timedelta, timezone
from fastapi import APIRouter
from app.classes.adapters.blink_api import BlinkAPI
from app.classes.adapters.config_aws import ConfigAWS
from app.classes.adapters.telegram_api import TelegramApi

CAM_ID = {}

router = APIRouter()
""" This creates the new API path /arm/{newtork_id} """


@router.get("/{channel_id}/{cam_name}")
def get_images(channel_id: str, cam_name: str):
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
    cam_array = config_instance.cameras
    blink_instance = BlinkAPI(config_instance)
    blink_instance.__set_token__()
    blink_instance.get_server()
    telegram_instance = TelegramApi(config_instance)

    # if is_cam(cam_name):
    #    thumb = get_camera_thumb(cam_name, blink_instance)
    # else:
    #    thumb = get_own_thumb(cam_name, blink_instance)
    camera_id = cam_array[cam_name]["id"]
    thumb = get_clip(blink_instance, camera_id, 500)
    if thumb == "":
        return {'response': "no hay videos"}
    clip_media = thumb['media']
    message = "Generado video de " + \
        thumb['device_name'] + \
        "("+thumb['network_name']+") a las " + thumb['created_at']
    response = telegram_instance.send_message(message, channel_id)
    video = blink_instance.get_clip(clip_media)
    video_clip = b''.join(chunk for chunk in video if chunk)
    response = telegram_instance.send_video(video_clip, channel_id)
    return response


def get_clip(blink_instance, camera_id, delta):
    """
        Gets the clip of the camera and returns it

    Args:
        blink_instance (class): class of blink api
        camera_id (str): Camera id
        delta (int): Delta in minutes

    Returns:
        str: Path to the clip
    """
    formatted_date = get_date(delta)
    response = blink_instance.get_video_events(formatted_date)
    for clip in response['response']['media']:
        if clip['device_id'] == int(camera_id):
            response = clip
            return response
    return ''


def get_date(delta, app_timezone=1):
    """
        Gets the date in the format that the blink api needs

    Args:
        delta (int): Minutes to substract from now.
    Returns:
        str: Date
    """
    european_timezone = timezone(timedelta(hours=app_timezone))
    now = datetime.now(european_timezone) - timedelta(minutes=delta)
    formatted_date = now.strftime('%Y-%m-%dT%H:%M:%S+0000')
    formatted_date = formatted_date.replace(':', '%3A')
    return formatted_date


def get_own_thumb(cam_name, blink_instance):
    """
        Gets the uri of the thumbnail of the owl and returns it

    Args:
        cam_name (str): name of the camera
        blink_instance (class): class of the blink api

    Returns:
        str: uri of the thumbnail
    """
    path = ''
    owl_id = CAM_ID[cam_name]["id"]
    response = blink_instance.set_owl_thumbnail(owl_id)
    response = blink_instance.get_home_screen_info()
    for owl in response['response']['owls']:
        if owl['id'] == int(owl_id):
            path = owl['thumbnail']
    return path


def get_camera_thumb(cam_name, blink_instance):
    """
        Gets the uri of the thumbnail of the camera and returns it

    Args:
        cam_name (str): name of the camera
        blink_instance (class): class of the blink api

    Returns:
        str: uri of the thumbnail
    """
    path = ''
    cam_id = CAM_ID[cam_name]["id"]
    response = blink_instance.set_thumbnail(cam_id)
    response = blink_instance.get_home_screen_info()
    for camera in response['response']['cameras']:
        if camera['id'] == int(cam_id):
            path = camera['thumbnail']
    return path


def is_cam(cam_name):
    """
     Determinates if the camera is a cam or a owl

    Args:
        cam_name (str): Name of the camera
    Returns:
        bool : True if it is a camera, false if it is a owl
    """
    return CAM_ID[cam_name]["type"] == "cam"
