"""
This file contains the endpoint to register a face by uploading an image file.
"""
# pylint: disable=E0401,R0801,E0611

from fastapi import APIRouter, File, UploadFile
from app.classes.adapters.config_aws import ConfigAWS
from app.classes.adapters.person_detector_rekognition import PersonDetectorRekognition

router = APIRouter()


@router.post("/{person_name}")
async def upload_face(person_name: str, image: UploadFile = File(...)):
    """
        Registers a face from an uploaded image file.

    Args:
        person_name (str): Name to associate with the face
        image (UploadFile): Image file containing the face

    Returns:
        dict: Registration result
    """
    contents = await image.read()
    if not contents:
        return {"status_code": 400, "is_ok": False,
                "response": "Empty image file"}

    config_instance = ConfigAWS()
    detector = PersonDetectorRekognition(config_instance)
    return detector.register_face(contents, person_name)
