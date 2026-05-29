"""Endpoint to download the latest local video clip for a camera."""
# pylint: disable=E0401

from typing import Iterator

from fastapi import APIRouter
from fastapi.responses import JSONResponse, StreamingResponse

from app.classes.adapters.blink_api import BlinkAPI
from app.classes.adapters.config_aws import ConfigAWS

router = APIRouter()


def _sanitize_filename(value: str) -> str:
    """Convert text into a filesystem-safe ASCII-ish fragment."""
    return (
        value.replace(" ", "_")
        .replace(":", "-")
        .replace("/", "-")
        .replace("\\", "-")
    )


def _build_download_filename(cam_name: str, created_at: str) -> str:
    """Create a deterministic filename for the downloaded clip."""
    return f"{_sanitize_filename(cam_name)}_{_sanitize_filename(created_at)}.mp4"


def _iter_non_empty(video_stream: Iterator[bytes]) -> Iterator[bytes]:
    """Yield only non-empty chunks from Blink streaming response."""
    for chunk in video_stream:
        if chunk:
            yield chunk


def _error_response(status_code: int, message: str):
    """Return unified error payload for v2 responses."""
    return JSONResponse(
        status_code=status_code,
        content={"status_code": status_code, "is_ok": False, "response": message},
    )


def _get_sync_module_id(blink_instance: BlinkAPI, camera_id: int) -> int:
    """Resolve sync module id for the provided camera id."""
    response = blink_instance.get_home_screen_info()
    cameras = response["response"]["cameras"]
    sync_modules = response["response"]["sync_modules"]
    network_id = 1
    for camera in cameras:
        if camera["id"] == int(camera_id):
            network_id = camera["network_id"]
            break
    for sync_module in sync_modules:
        if sync_module["network_id"] == network_id:
            return int(sync_module["id"])
    return 1


@router.get("/{cam_name}")
def get_local_video(cam_name: str):
    """Download latest local-storage clip as an MP4 attachment."""
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

    sync_module_id = _get_sync_module_id(blink_instance, int(camera_id))
    manifest_response = blink_instance.get_local_clips(sync_module_id)
    clips = manifest_response.get("response", {})
    clip_list = clips.get("clips", [])

    if not clip_list:
        return _error_response(404, "No hay videos")

    video = blink_instance.get_local_clip(clips)
    if isinstance(video, dict):
        status_code = int(video.get("status_code", 500))
        return JSONResponse(status_code=status_code, content=video)

    clip = clip_list[0]
    filename = _build_download_filename(
        clip.get("camera_name", cam_name),
        clip.get("created_at", "latest"),
    )
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "X-Blink-Camera": str(clip.get("camera_name", cam_name)),
        "X-Blink-Created-At": str(clip.get("created_at", "")),
    }

    return StreamingResponse(
        _iter_non_empty(video),
        media_type="video/mp4",
        headers=headers,
    )
