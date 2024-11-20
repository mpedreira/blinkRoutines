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
EMPTY = ""

router = APIRouter()
""" This creates the new API path /arm/{newtork_id} """


@router.get("/{channel_id}/{cam_name}")
def get_local_video(channel_id: str, cam_name: str):
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
    camera_id = cam_array[cam_name]["id"]
    clips = get_clip(blink_instance, camera_id, 5)
    numero_clips = len(clips)
    if numero_clips == 0:
        response = {}
        response['status_code'] = 404
        response['is_success'] = False
        response['response'] = "No hay videos"
        return response
    clip = clips[0]
    clip_media = clip['media']
    message = "Generado video de " + clip['device_name'] + "("+clip['network_name']+") a las " + \
        clip['created_at'] + " hay " + \
        str(numero_clips) + " clips en total en esa franja"
    response = telegram_instance.send_message(message, channel_id)
    video = blink_instance.get_clip(clip_media)
    if isinstance(video, dict):
        message = "No he sido capaz de descargar el video"
        response = telegram_instance.send_message(message, channel_id)
        return response
    video_clip = b''.join(chunk for chunk in video if chunk)
    response = telegram_instance.send_message(message, channel_id)
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
    clips = []
    for clip in response['response']['media']:
        if clip['device_id'] == int(camera_id):
            clips.append(clip)
    return clips


def get_date(delta, app_timezone=0):
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
