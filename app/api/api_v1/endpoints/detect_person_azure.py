"""
This file contains the endpoint to detect persons from a camera image using Azure Face API.
"""
# pylint: disable=E0401,R0801,E0611

from datetime import datetime
from time import sleep
from fastapi import APIRouter
from app.classes.adapters.blink_api import BlinkAPI
from app.classes.adapters.config_azure import ConfigAzure
from app.classes.adapters.telegram_api import TelegramApi
from app.classes.adapters.person_detector_azure import PersonDetectorAzure
from app.classes.person_detector import UNKNOWN_PERSON, FACE_CONFIDENCE_THRESHOLD

EMPTY = ""
THUMB_WAIT_SECONDS = 20

router = APIRouter()


@router.get("/{channel_id}/{cam_name}")
def detect_person_azure(channel_id: str, cam_name: str):
    config_instance = ConfigAzure()
    cam = config_instance.cameras.get(cam_name)
    if not cam or not cam.get('id'):
        return {"status_code": 400, "is_ok": False,
                "response": f"Camera '{cam_name}' not found or has no configured id"}

    blink_instance = BlinkAPI(config_instance)
    blink_instance.__set_token__()
    blink_instance.get_server()

    path = get_fresh_thumb(blink_instance, cam['id'], cam['type'])
    if path is None:
        response = f"Blink no ha podido actualizar el thumbnail de ' + \
            {cam_name}', posible throttling"
        return {"status_code": 429, "is_ok": False, "response": response}
    if not path:
        return {"status_code": 404, "is_ok": False,
                "response": f"Could not get thumbnail for '{cam_name}'"}

    thumb = blink_instance.get_image(path)
    faces = PersonDetectorAzure(config_instance).detect_faces(thumb)
    message = build_message(
        cam_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), faces)

    telegram_instance = TelegramApi(config_instance)
    telegram_instance.send_message(message, channel_id)
    return telegram_instance.send_image_from_bytes(thumb, channel_id)


def get_fresh_thumb(blink_instance, camera_id, cam_type):
    if cam_type == 'owl':
        trigger = blink_instance.set_owl_thumbnail(camera_id)
    else:
        trigger = blink_instance.set_thumbnail(camera_id)
    if not trigger.get('is_ok'):
        return None
    sleep(THUMB_WAIT_SECONDS)
    response = blink_instance.get_home_screen_info()
    key = 'cameras' if cam_type == 'cam' else 'owls'
    for device in response['response'].get(key, []):
        if device['id'] == int(camera_id):
            return device['thumbnail']
    return EMPTY


def build_message(cam_name, date, faces):
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
