"""
    This includes all the endpoints of the API Rest
"""
# pylint: disable=E0401

from fastapi import APIRouter

from .endpoints import arm, disarm, update_owl, update_thumb, get_basic_config, send_2fa

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
