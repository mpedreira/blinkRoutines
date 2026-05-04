"""
This file contains the endpoint to register a face from a camera image using Azure Face API.
"""
# pylint: disable=E0401,R0801,E0611

from time import sleep
from fastapi import APIRouter
from app.classes.adapters.blink_api import BlinkAPI
from app.classes.adapters.config_azure import ConfigAzure
from app.classes.adapters.person_detector_azure import PersonDetectorAzure

EMPTY = ""

router = APIRouter()


@router.post("/{person_name}/{cam_name}")
def register_face_azure(person_name: str, cam_name: str):
    config_instance = ConfigAzure()
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
    detector = PersonDetectorAzure(config_instance)
    return detector.register_face(thumb, person_name)


def get_camera_thumb(blink_instance, camera_id):
    blink_instance.set_thumbnail(camera_id)
    sleep(5)
    response = blink_instance.get_home_screen_info()
    for camera in response['response']['cameras']:
        if camera['id'] == int(camera_id):
            return camera['thumbnail']
    return EMPTY


def get_owl_thumb(blink_instance, camera_id):
    blink_instance.set_owl_thumbnail(camera_id)
    sleep(5)
    response = blink_instance.get_home_screen_info()
    for owl in response['response']['owls']:
        if owl['id'] == int(camera_id):
            return owl['thumbnail']
    return EMPTY
