"""
This file contains the endpoint to get the images from the cameras in telegram
"""
# pylint: disable=E0401,R0801,E0611

from fastapi import APIRouter
from app.classes.adapters.blink_api import BlinkAPI
from app.classes.adapters.config_aws import ConfigAWS
from app.classes.adapters.telegram_api import TelegramApi

router = APIRouter()


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

    camera_id = cam_array.get(cam_name, {}).get("id")
    if not camera_id:
        return {"status_code": 400, "is_ok": False,
                "response": f"Camera '{cam_name}' not found or has no configured id"}
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
    if isinstance(video, dict):
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
