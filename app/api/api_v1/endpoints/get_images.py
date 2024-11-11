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
 #   clips = get_clip(blink_instance, camera_id, 5)
 #   numero_clips = len(clips)
 #   if numero_clips == 0:
 #       response['response'] = "No hay videos"
 #       response = {}
 #       return response
 #   thumb = clips[0]
 #   clip_media = thumb['media']
    # message = "Generado video de " + \
    #    thumb['device_name'] + \
    #    "("+thumb['network_name']+") a las " + thumb['created_at'] + \
    #    " hay " + str(numero_clips) + " clips en total en esa franja"
    # response = telegram_instance.send_message(message, channel_id)
    # video = blink_instance.get_clip(clip_media)

    sync_module = get_sync_module_id(blink_instance, camera_id)
    response = blink_instance.get_local_clips(sync_module)
    clips = response['response']
    numero_clips = len(clips['clips'])
    if numero_clips == 0:
        response = {}
        response['response'] = "No hay videos"
        return response
    video = blink_instance.get_local_clip(clips)
    clip = clips['clips'][0]
    if type(video) == dict:
        message = "No he sido capaz de descargar el video"
        response = telegram_instance.send_message(message, channel_id)
        return response
    video_clip = b''.join(chunk for chunk in video if chunk)
    message = "Generado video de " + \
        clip['camera_name'] + \
        " a las " + clip['created_at'] + \
        " hay " + str(numero_clips) + " clips en total en esa franja"
    response = telegram_instance.send_message(message, channel_id)

    response = telegram_instance.send_video(video_clip, channel_id)
    return response


def get_sync_module_id(blink_instance, camera_id):
    """
        Gets the sync module id asociated to the camera

    Args:
        blink_instance (class): Instance of the blink api
        camera_id (int): camera id

    Returns:
        int: sync module id
    """
    response = blink_instance.get_home_screen_info()
    network_id = 1
    sync_module_id = 1
    cameras = response['response']['cameras']
    sync_modules = response['response']['sync_modules']
    network_id = get_network_id(camera_id, cameras)
    sync_module_id = get_sync_module_from_network_id(network_id, sync_modules)
    return sync_module_id


def get_sync_module_from_network_id(network_id, sync_modules):
    """
        Gets the sync module id from the network id

    Args:
        network_id (int): network id
        sync_modules (int): sync module list

    Returns:
        int: sync module id
    """
    sync_module_id = 1
    for sync_module in sync_modules:
        if sync_module['network_id'] == network_id:
            sync_module_id = sync_module['id']
            return sync_module_id
    return sync_module_id


def get_network_id(camera_id, cameras):
    """
        Gets the network id from the camera id
    Args:
        camera_id (int): camera id
        cameras (dict): list of cameras in the account

    Returns:
        int: network id
    """
    network_id = 1
    for camera in cameras:
        if camera['id'] == int(camera_id):
            network_id = camera['network_id']
            return network_id
    return network_id


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
