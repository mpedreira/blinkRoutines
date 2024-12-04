"""
    This includes all the endpoints of the API Rest
"""
# pylint: disable=E0401,E0611

from fastapi import APIRouter

from .endpoints import arm, disarm, get_image, get_local_video, update_owl, update_thumb
from .endpoints import get_basic_config, send_2fa, telegram, save_images, get_remote_video
from .endpoints import entrance

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
router.include_router(entrance.router,
                      prefix="/entrance", tags=["Entrance"])
