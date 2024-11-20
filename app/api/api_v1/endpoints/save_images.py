"""
This file contains the endpoint to get the images from the cameras in telegram
"""
# pylint: disable=E0401,R0801,E0611

from datetime import datetime
from fastapi import APIRouter
from app.classes.adapters.blink_api import BlinkAPI
from app.classes.adapters.config_aws import ConfigAWS
from app.classes.adapters.storage_s3_aws import StorageS3AWS


router = APIRouter()
""" This creates the new API path /arm/{newtork_id} """


@router.get("/{cam_name}")
def get_images(cam_name: str):
    """
        Function that calls the BlinkAPI class, gets the thumb and send it to S3 Storage

    Args:
        cam_name (str): Name of the camera to get the thumb

    Returns:
        dict : This responses a json with the status_code, 
        the response of the server(blank if has no json format) and if is_success
    """
    config_instance = ConfigAWS()
    cam_array = config_instance.cameras
    blink_instance = BlinkAPI(config_instance)
    s3_instance = StorageS3AWS(config_instance)
    blink_instance.__set_token__()
    blink_instance.get_server()
    camera_id = cam_array[cam_name]['id']
    cam_type = cam_array[cam_name]['type']
    s3_path = config_instance.s3_folder
    if is_camera(cam_type):
        blink_instance.set_thumbnail(camera_id)
        response = blink_instance.get_home_screen_info()
        for camera in response['response']['cameras']:
            if camera['id'] == int(camera_id):
                path = camera['thumbnail']
    else:
        blink_instance.set_owl_thumbnail(camera_id)
        response = blink_instance.get_home_screen_info()
        for owl in response['response']['owl']:
            if owl['id'] == int(camera_id):
                path = owl['thumbnail']

    thumb = blink_instance.get_image(path)
    date = datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
    file_name = s3_path + cam_name + "_" + date + ".jpg"
    response = s3_instance.put_object(thumb, file_name)
    return {"status_code": 200, "response": response, "is_success": True}


def is_camera(cam_type):
    """
        Decides if the camera is a camera or a owl

    Args:
        cam_type (str): type of the camera

    Returns:
        bool: True if it is a cam, False if it is a owl
    """
    if cam_type == "cam":
        return True
    return False
