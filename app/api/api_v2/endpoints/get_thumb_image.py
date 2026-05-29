"""Endpoint to download camera thumbnail as an image."""
# pylint: disable=E0401

from time import sleep

from fastapi import APIRouter
from fastapi.responses import JSONResponse, StreamingResponse

from app.classes.adapters.blink_api import BlinkAPI
from app.classes.adapters.config_aws import ConfigAWS

router = APIRouter()


def _error_response(status_code: int, message: str):
    """Return unified error payload for v2 responses."""
    return JSONResponse(
        status_code=status_code,
        content={"status_code": status_code, "is_ok": False, "response": message},
    )


def _resolve_thumb_path(blink_instance: BlinkAPI, camera_id: int, cam_type: str) -> str:
    """Try to refresh thumbnail and resolve current thumbnail path from home screen data."""
    if cam_type == "owl":
        trigger = blink_instance.set_owl_thumbnail(str(camera_id))
    else:
        trigger = blink_instance.set_thumbnail(str(camera_id))

    if isinstance(trigger, dict) and trigger.get("is_ok"):
        sleep(5)

    response = blink_instance.get_home_screen_info().get("response", {})
    if cam_type == "owl":
        devices = response.get("owls", []) or response.get("owl", [])
    else:
        devices = response.get("cameras", [])

    for device in devices:
        if int(device.get("id", -1)) == int(camera_id):
            return str(device.get("thumbnail", ""))
    return ""


@router.get("/{cam_name}")
def get_thumb_image(cam_name: str):
    """Download current thumbnail as image/jpeg for a configured camera."""
    config_instance = ConfigAWS()
    camera = config_instance.cameras.get(cam_name, {})
    camera_id = camera.get("id")
    if not camera_id:
        return _error_response(
            400,
            f"Camera '{cam_name}' not found or has no configured id",
        )

    blink_instance = BlinkAPI(config_instance)
    blink_instance.__set_token__()
    blink_instance.get_server()

    path = _resolve_thumb_path(
        blink_instance=blink_instance,
        camera_id=int(camera_id),
        cam_type=str(camera.get("type", "cam")),
    )
    if not path:
        return _error_response(404, f"Could not get thumbnail for '{cam_name}'")

    thumb = blink_instance.get_image(path)
    if not thumb:
        return _error_response(404, f"Could not download thumbnail for '{cam_name}'")

    return StreamingResponse(
        iter([thumb]),
        media_type="image/jpeg",
        headers={"X-Blink-Camera": str(cam_name)},
    )
