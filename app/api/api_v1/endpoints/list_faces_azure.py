"""
This file contains the endpoint to list registered faces using Azure Face API.
"""
# pylint: disable=E0401,R0801,E0611

from fastapi import APIRouter
from app.classes.adapters.config_azure import ConfigAzure

router = APIRouter()


@router.get("")
def list_faces_azure():
    from app.classes.adapters.person_detector_azure import PersonDetectorAzure

    config_instance = ConfigAzure()
    detector = PersonDetectorAzure(config_instance)
    return detector.list_faces()
