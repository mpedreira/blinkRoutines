"""
This file contains the endpoint to register a face by uploading an image file using Azure Face API.
"""
# pylint: disable=E0401,R0801,E0611

from fastapi import APIRouter, File, UploadFile
from app.classes.adapters.config_azure import ConfigAzure
from app.classes.adapters.person_detector_azure import PersonDetectorAzure

router = APIRouter()


@router.post("/{person_name}")
async def upload_face_azure(person_name: str, image: UploadFile = File(...)):
    contents = await image.read()
    if not contents:
        return {"status_code": 400, "is_ok": False,
                "response": "Empty image file"}

    config_instance = ConfigAzure()
    detector = PersonDetectorAzure(config_instance)
    return detector.register_face(contents, person_name)
