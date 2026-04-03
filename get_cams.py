"""Script for testing Blink local video retrieval and Telegram delivery."""
from app.classes.adapters.blink_api import BlinkAPI
from app.classes.adapters.config_aws import ConfigAWS
from app.classes.adapters.telegram_api import TelegramApi


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


def _send_clip(telegram_instance, blink_instance, clips, channel_id):
    """Download the first clip and send it to Telegram."""
    numero_clips = len(clips['clips'])
    if numero_clips == 0:
        print("No hay videos")
        return
    video = blink_instance.get_local_clip(clips)
    clip = clips['clips'][0]
    if isinstance(video, dict):
        telegram_instance.send_message(
            "No he sido capaz de descargar el video", channel_id)
        return
    video_clip = b''.join(chunk for chunk in video if chunk)
    message = (
        "Generado video de " + clip['camera_name'] +
        " a las " + clip['created_at'] +
        " hay " + str(numero_clips) + " clips en total en esa franja"
    )
    telegram_instance.send_message(message, channel_id)
    telegram_instance.send_video(video_clip, channel_id)


def main():
    """Entry point: fetch local clip and send to Telegram."""
    config_instance = ConfigAWS()
    blink_instance = BlinkAPI(config_instance)
    telegram_instance = TelegramApi(config_instance)

    blink_instance.__set_token__()
    blink_instance.get_server()
    blink_instance.set_thumbnail('566211')

    channel_id = "-4572906427"
    cam_name = "Entrada"
    camera_id = config_instance.cameras[cam_name]["id"]
    sync_module = get_sync_module_id(blink_instance, camera_id)
    response = blink_instance.get_local_clips(sync_module)
    clips = response['response']
    _send_clip(telegram_instance, blink_instance, clips, channel_id)


if __name__ == '__main__':
    main()
