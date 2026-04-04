"""
This file contains the endpoint to delete all faces registered under a person name.
"""
# pylint: disable=E0401,R0801,E0611

from fastapi import APIRouter
from app.classes.adapters.config_aws import ConfigAWS
from app.classes.adapters.person_detector_rekognition import PersonDetectorRekognition

router = APIRouter()


@router.delete("/{person_name}")
def delete_face(person_name: str):
    """
        Deletes all faces registered under the given person name
        from the Rekognition collection.

    Args:
        person_name (str): Name of the person to remove

    Returns:
        dict: Result with deleted_count
    """
    config_instance = ConfigAWS()
    detector = PersonDetectorRekognition(config_instance)
    return detector.delete_face(person_name)
