"""
This file contains the endpoint to list registered faces using Face++ API.
"""
# pylint: disable=E0401,R0801,E0611

from fastapi import APIRouter
from app.classes.adapters.config_facepp import ConfigFacePP
from app.classes.adapters.person_detector_facepp import PersonDetectorFacePP

router = APIRouter()


@router.get("")
def list_faces_facepp():
    config_instance = ConfigFacePP()
    detector = PersonDetectorFacePP(config_instance)
    return detector.list_faces()
