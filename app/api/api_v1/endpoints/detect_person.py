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
from app.classes.person_detector import UNKNOWN_PERSON, FACE_CONFIDENCE_THRESHOLD

EMPTY = ""
THUMB_WAIT_SECONDS = 5

router = APIRouter()


@router.get("/{channel_id}/{cam_name}")
def detect_person(channel_id: str, cam_name: str):
    """
        Forces a new thumbnail on the camera, waits for it to be ready,
        runs face detection, and sends the result to a Telegram channel.

    Args:
        channel_id (str): ID of the telegram channel
        cam_name (str): Name of the camera

    Returns:
        dict: Telegram API response
    """
    config_instance = ConfigAWS()
    cam = config_instance.cameras.get(cam_name)
    if not cam or not cam.get('id'):
        return {"status_code": 400, "is_ok": False,
                "response": f"Camera '{cam_name}' not found or has no configured id"}

    blink_instance = BlinkAPI(config_instance)
    blink_instance.__set_token__()
    blink_instance.get_server()

    path = get_fresh_thumb(blink_instance, cam['id'], cam['type'])
    if not path:
        return {"status_code": 404, "is_ok": False,
                "response": f"Could not get thumbnail for '{cam_name}'"}

    thumb = blink_instance.get_image(path)
    faces = PersonDetectorRekognition(config_instance).detect_faces(thumb)
    message = build_message(
        cam_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), faces)

    telegram_instance = TelegramApi(config_instance)
    telegram_instance.send_message(message, channel_id)
    return telegram_instance.send_image_from_bytes(thumb, channel_id)


def get_fresh_thumb(blink_instance, camera_id, cam_type):
    """
    Forces a new thumbnail capture then reads it from the homescreen.
    Uses set_owl_thumbnail for owl devices, set_thumbnail for cameras.

    Args:
        blink_instance: Blink API instance
        camera_id (str): Camera id
        cam_type (str): 'cam' or 'owl'

    Returns:
        str: Thumbnail path, or empty string if not found
    """
    if cam_type == 'owl':
        blink_instance.set_owl_thumbnail(camera_id)
    else:
        blink_instance.set_thumbnail(camera_id)
    sleep(THUMB_WAIT_SECONDS)
    response = blink_instance.get_home_screen_info()
    key = 'cameras' if cam_type == 'cam' else 'owls'
    for device in response['response'].get(key, []):
        if device['id'] == int(camera_id):
            return device['thumbnail']
    return EMPTY


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
        if name == UNKNOWN_PERSON or confidence < FACE_CONFIDENCE_THRESHOLD:
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
