"""
    This includes all the endpoints of the API Rest
"""
# pylint: disable=E0401,E0611

from fastapi import APIRouter

from .endpoints import arm, disarm, get_image, get_local_video, update_owl, update_thumb
from .endpoints import get_basic_config, send_2fa, telegram, save_images, get_remote_video
from .endpoints import detect_person, register_face, list_faces
from .endpoints import train_face, upload_face, delete_face
from .endpoints import (
    detect_person_azure,
    register_face_azure,
    list_faces_azure,
    upload_face_azure,
    delete_face_azure,
)
from .endpoints import (
    detect_person_facepp,
    register_face_facepp,
    list_faces_facepp,
    upload_face_facepp,
    delete_face_facepp,
)


router = APIRouter()
router.include_router(get_basic_config.router,
                      prefix="/basic_config", tags=["Config"])
router.include_router(send_2fa.router,
                      prefix="/mfa", tags=["Config"])
router.include_router(update_thumb.router,
                      prefix="/update_thumb", tags=["Camera"])
router.include_router(update_owl.router,
                      prefix="/update_owl", tags=["Owl"])
router.include_router(arm.router, prefix="/arm", tags=["Network"])
router.include_router(disarm.router, prefix="/disarm", tags=["Network"])
router.include_router(telegram.router, prefix="/telegram", tags=["Network"])
router.include_router(get_local_video.router,
                      prefix="/get_local_video", tags=["Camera"])
router.include_router(get_remote_video.router,
                      prefix="/get_remote_video", tags=["Camera"])
router.include_router(get_image.router, prefix="/get_image", tags=["Camera"])
router.include_router(save_images.router,
                      prefix="/save_images", tags=["Camera"])
router.include_router(detect_person.router,
                      prefix="/detect_person", tags=["Detection"])
router.include_router(register_face.router,
                      prefix="/register_face", tags=["Detection"])
router.include_router(list_faces.router,
                      prefix="/list_faces", tags=["Detection"])
router.include_router(train_face.router,
                      prefix="/train_face", tags=["Detection"])
router.include_router(upload_face.router,
                      prefix="/upload_face", tags=["Detection"])
router.include_router(delete_face.router,
                      prefix="/delete_face", tags=["Detection"])
router.include_router(detect_person_azure.router,
                      prefix="/v2/detect_person", tags=["Detection v2"])
router.include_router(register_face_azure.router,
                      prefix="/v2/register_face", tags=["Detection v2"])
router.include_router(list_faces_azure.router,
                      prefix="/v2/list_faces", tags=["Detection v2"])
router.include_router(upload_face_azure.router,
                      prefix="/v2/upload_face", tags=["Detection v2"])
router.include_router(delete_face_azure.router,
                      prefix="/v2/delete_face", tags=["Detection v2"])
router.include_router(detect_person_facepp.router,
                      prefix="/v3/detect_person", tags=["Detection v3"])
router.include_router(register_face_facepp.router,
                      prefix="/v3/register_face", tags=["Detection v3"])
router.include_router(list_faces_facepp.router,
                      prefix="/v3/list_faces", tags=["Detection v3"])
router.include_router(upload_face_facepp.router,
                      prefix="/v3/upload_face", tags=["Detection v3"])
router.include_router(delete_face_facepp.router,
                      prefix="/v3/delete_face", tags=["Detection v3"])
