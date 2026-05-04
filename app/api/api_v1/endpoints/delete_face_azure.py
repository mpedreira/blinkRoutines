"""
This file contains the endpoint to delete all faces registered under a person name
using Azure Face API.
"""
# pylint: disable=E0401,R0801,E0611

from fastapi import APIRouter
from app.classes.adapters.config_azure import ConfigAzure
from app.classes.adapters.person_detector_azure import PersonDetectorAzure

router = APIRouter()


@router.delete("/{person_name}")
def delete_face_azure(person_name: str):
    """
        Deletes all Person entries registered under the given person name
        from the Azure Face PersonGroup.

    Args:
        person_name (str): Name of the person to remove

    Returns:
        dict: Result with deleted_count
    """
    config_instance = ConfigAzure()
    detector = PersonDetectorAzure(config_instance)
    return detector.delete_face(person_name)
