"""
This file contains the endpoint to train the model with the current camera thumbnail.
Unlike register_face, this does NOT force a new thumbnail capture — it uses
the existing one (e.g. from the last motion detection).
"""
# pylint: disable=E0401,R0801,E0611

from fastapi import APIRouter
from app.classes.adapters.blink_api import BlinkAPI
from app.classes.adapters.config_aws import ConfigAWS
from app.classes.adapters.person_detector_rekognition import PersonDetectorRekognition

EMPTY = ""

router = APIRouter()


@router.post("/{person_name}/{cam_name}")
def train_face(person_name: str, cam_name: str):
    """
        Takes the current thumbnail of a camera (without refreshing it)
        and registers the face with the given person name.
        Useful for training unknown faces after a detection event.

    Args:
        person_name (str): Name to associate with the face
        cam_name (str): Camera to take the existing thumbnail from

    Returns:
        dict: Registration result
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
    path = get_current_thumb(blink_instance, camera_id, cam_type)

    if not path:
        return {"status_code": 404, "is_ok": False,
                "response": f"No thumbnail available for '{cam_name}'"}

    thumb = blink_instance.get_image(path)
    detector = PersonDetectorRekognition(config_instance)
    result = detector.register_face(thumb, person_name)
    return result


def get_current_thumb(blink_instance, camera_id, cam_type):
    """
        Gets the current thumbnail path without forcing a refresh.

    Args:
        blink_instance (class): Blink API instance
        camera_id (str): Camera id
        cam_type (str): 'cam' or 'owl'

    Returns:
        str: Path of the current thumbnail
    """
    response = blink_instance.get_home_screen_info()
    if cam_type == "cam":
        for camera in response['response']['cameras']:
            if camera['id'] == int(camera_id):
                return camera['thumbnail']
    else:
        for owl in response['response']['owls']:
            if owl['id'] == int(camera_id):
                return owl['thumbnail']
    return EMPTY
