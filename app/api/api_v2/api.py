"""API v2 router registration."""

from fastapi import APIRouter

from .endpoints import get_local_video, get_thumb_image


router = APIRouter()
router.include_router(get_local_video.router,
                      prefix="/get_local_video", tags=["Camera v2"])
router.include_router(get_thumb_image.router,
                      prefix="/get_thumb_image", tags=["Camera v2"])
