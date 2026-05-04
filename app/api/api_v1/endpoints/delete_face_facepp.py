"""
This file contains the endpoint to delete all faces registered under a person name
using Face++ API.
"""
# pylint: disable=E0401,R0801,E0611

from fastapi import APIRouter
from app.classes.adapters.config_facepp import ConfigFacePP
from app.classes.adapters.person_detector_facepp import PersonDetectorFacePP

router = APIRouter()


@router.delete("/{person_name}")
def delete_face_facepp(person_name: str):
    """
        Removes all face_tokens associated with person_name from the Face++ FaceSet.

    Args:
        person_name (str): Name of the person to remove

    Returns:
        dict: Result with deleted_count
    """
    config_instance = ConfigFacePP()
    detector = PersonDetectorFacePP(config_instance)
    return detector.delete_face(person_name)
