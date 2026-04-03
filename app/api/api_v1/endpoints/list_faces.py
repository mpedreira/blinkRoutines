"""
This file contains the endpoint to list registered faces in the collection.
"""
# pylint: disable=E0401,R0801,E0611

from fastapi import APIRouter
from app.classes.adapters.config_aws import ConfigAWS
from app.classes.adapters.person_detector_rekognition import PersonDetectorRekognition

router = APIRouter()


@router.get("")
def list_faces():
    """
        Lists all registered faces in the Rekognition collection.

    Returns:
        dict: Collection info with face_count and faces list
    """
    config_instance = ConfigAWS()
    detector = PersonDetectorRekognition(config_instance)
    return detector.list_faces()
