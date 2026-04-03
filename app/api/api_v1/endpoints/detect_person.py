"""
This file contains the endpoint to detect persons from a camera image.
"""
# pylint: disable=E0401,R0801,E0611

from datetime import datetime
from time import sleep
from fastapi import APIRouter
from app.classes.adapters.blink_api import BlinkAPI
from app.classes.adapters.config_aws import ConfigAWS
from app.classes.adapters.telegram_api import TelegramApi
from app.classes.adapters.person_detector_rekognition import PersonDetectorRekognition
from app.classes.person_detector import UNKNOWN_PERSON

EMPTY = ""

router = APIRouter()


@router.get("/{channel_id}/{cam_name}")
def detect_person(channel_id: str, cam_name: str):
    """
        Gets the thumbnail from a camera, runs face detection,
        and sends the result to a Telegram channel.

    Args:
        channel_id (str): ID of the telegram channel
        cam_name (str): Name of the camera

    Returns:
        dict: Telegram API response
    """
    config_instance = ConfigAWS()
    cam_array = config_instance.cameras
    cam = cam_array.get(cam_name)
    if not cam or not cam.get('id'):
        return {"status_code": 400, "is_ok": False,
                "response": f"Camera '{cam_name}' not found or has no configured id"}

    blink_instance = BlinkAPI(config_instance)
    blink_instance.__set_token__()
    blink_instance.get_server()

    camera_id = cam['id']
    cam_type = cam['type']
    if cam_type == "cam":
        path = get_camera_thumb(blink_instance, camera_id)
    else:
        path = get_owl_thumb(blink_instance, camera_id)

    if not path:
        return {"status_code": 404, "is_ok": False,
                "response": f"Could not get thumbnail for '{cam_name}'"}

    thumb = blink_instance.get_image(path)
    detector = PersonDetectorRekognition(config_instance)
    faces = detector.detect_faces(thumb)

    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = build_message(cam_name, date, faces)

    telegram_instance = TelegramApi(config_instance)
    telegram_instance.send_message(message, channel_id)
    response = telegram_instance.send_image_from_bytes(thumb, channel_id)
    return response


def build_message(cam_name, date, faces):
    """
        Builds the notification message from detected faces.
        Groups duplicates by name keeping the highest confidence,
        and treats matches below 80% as unknown.

    Args:
        cam_name (str): Camera name
        date (str): Detection timestamp
        faces (list): List of detected faces with name and confidence

    Returns:
        str: Formatted message
    """
    if not faces:
        return f"[{date}] No se detectaron personas en {cam_name}"

    best_by_name = {}
    unknown_count = 0
    for face in faces:
        name = face['name']
        confidence = face['confidence']
        if name == UNKNOWN_PERSON or confidence < 80:
            unknown_count += 1
            continue
        if name not in best_by_name or confidence > best_by_name[name]:
            best_by_name[name] = confidence

    parts = []
    for name, confidence in best_by_name.items():
        parts.append(
            f"{name} detectado en {cam_name} "
            f"con probabilidad de acierto {confidence}%"
        )
    for _ in range(unknown_count):
        parts.append(f"Persona desconocida detectada en {cam_name}")

    return f"[{date}] " + ". ".join(parts)


def get_camera_thumb(blink_instance, camera_id):
    """
        Gets the thumbnail path of a camera.

    Args:
        blink_instance (class): Blink API instance
        camera_id (str): Camera id

    Returns:
        str: Path of the thumbnail
    """
    blink_instance.set_thumbnail(camera_id)
    sleep(5)
    response = blink_instance.get_home_screen_info()
    for camera in response['response']['cameras']:
        if camera['id'] == int(camera_id):
            return camera['thumbnail']
    return EMPTY


def get_owl_thumb(blink_instance, camera_id):
    """
        Gets the thumbnail path of an owl.

    Args:
        blink_instance (class): Blink API instance
        camera_id (str): Camera id

    Returns:
        str: Path of the thumbnail
    """
    blink_instance.set_owl_thumbnail(camera_id)
    sleep(5)
    response = blink_instance.get_home_screen_info()
    for owl in response['response']['owls']:
        if owl['id'] == int(camera_id):
            return owl['thumbnail']
    return EMPTY
