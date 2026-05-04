"""
This file contains the endpoint to register a face by uploading an image file using Face++ API.
"""
# pylint: disable=E0401,R0801,E0611

from fastapi import APIRouter, File, UploadFile
from app.classes.adapters.config_facepp import ConfigFacePP
from app.classes.adapters.person_detector_facepp import PersonDetectorFacePP

router = APIRouter()


@router.post("/{person_name}")
async def upload_face_facepp(person_name: str, image: UploadFile = File(...)):
    contents = await image.read()
    if not contents:
        return {"status_code": 400, "is_ok": False,
                "response": "Empty image file"}

    config_instance = ConfigFacePP()
    detector = PersonDetectorFacePP(config_instance)
    return detector.register_face(contents, person_name)
