from datetime import datetime, timedelta
from app.classes.adapters.blink_api import BlinkAPI
from app.classes.adapters.config_static_aws import ConfigStatic
from app.classes.adapters.telegram_api import TelegramApi
from app.classes.adapters.http_request_standard import HttpRequestStandard


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


config_instance = ConfigStatic()
blink_instance = BlinkAPI(config_instance)
telegram_instance = TelegramApi(config_instance)


def prepare_payload(config):
    payload = {}
    payload['config'] = config
    payload['headers'] = {
        'Content-Type': 'application/json'
    }
    payload['timeout'] = config.timeout
    payload['data'] = ''
    payload['auth'] = ''
    return payload


blink_instance.__set_token__()
blink_instance.get_server()
response = blink_instance.set_thumbnail('566211')
response = blink_instance.get_home_screen_info()
# Obtener la fecha y hora actual
now = datetime.utcnow() - timedelta(minutes=5)

# Formatear la fecha como "2024-10-28T09:58:14+0000"
formatted_date = now.strftime('%Y-%m-%dT%H:%M:%S+0000')

# Reemplazar ':' por '%3A' para que coincida con el formato solicitado
formatted_date = formatted_date.replace(':', '%3A')
channel_id = "-4572906427"
cam_name = "Entrada"
cam_array = config_instance.cameras
camera_id = cam_array[cam_name]["id"]
sync_module = get_sync_module_id(blink_instance, camera_id)
response = blink_instance.get_local_clips(sync_module)
clips = response['response']
numero_clips = len(clips['clips'])
if numero_clips == 0:
    response = {}
    response['response'] = "No hay videos"
video = blink_instance.get_local_clip(clips)
clip = clips['clips'][0]
if type(video) == dict:
    message = "No he sido capaz de descargar el video"
    response = telegram_instance.send_message(message, channel_id)
video_clip = b''.join(chunk for chunk in video if chunk)
message = "Generado video de " + \
    clip['camera_name'] + \
    " a las " + clip['created_at'] + \
    " hay " + str(numero_clips) + " clips en total en esa franja"
response = telegram_instance.send_message(message, channel_id)
response = telegram_instance.send_video(video_clip, channel_id)
