"""Endpoint to download the latest cloud video clip for a camera.

Uses the Blink media/changed API (cloud events) instead of local storage to
avoid the local-storage manifest polling that exceeds the API Gateway 29-second
hard timeout.
"""
# pylint: disable=E0401

from datetime import datetime, timedelta, timezone
from typing import Iterator

from fastapi import APIRouter
from fastapi.responses import JSONResponse, StreamingResponse

from app.classes.adapters.blink_api import BlinkAPI
from app.classes.adapters.config_aws import ConfigAWS

router = APIRouter()

_LOOK_BACK_MINUTES = 240  # search window for recent clips


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


def _since_date(minutes: int) -> str:
    """Return an ISO-8601 date string URL-encoded for the Blink media API."""
    since = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    raw = since.strftime("%Y-%m-%dT%H:%M:%S+0000")
    return raw.replace(":", "%3A").replace("+", "%2B")


@router.get("/{cam_name}")
def get_local_video(cam_name: str):
    """Stream the most recent cloud clip for *cam_name* as an MP4 attachment."""
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

    events_response = blink_instance.get_video_events(_since_date(_LOOK_BACK_MINUTES))
    media = events_response.get("response", {}).get("media", [])

    clips = [m for m in media if str(m.get("device_id")) == str(camera_id)]
    if not clips:
        return _error_response(404, f"No hay videos recientes para '{cam_name}'")

    clip = clips[0]
    video_stream = blink_instance.get_clip(clip["media"])
    if isinstance(video_stream, dict):
        status_code = int(video_stream.get("status_code", 500))
        return JSONResponse(status_code=status_code, content=video_stream)

    filename = _build_download_filename(
        clip.get("device_name", cam_name),
        clip.get("created_at", "latest"),
    )
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "X-Blink-Camera": str(clip.get("device_name", cam_name)),
        "X-Blink-Created-At": str(clip.get("created_at", "")),
    }

    return StreamingResponse(
        _iter_non_empty(video_stream),
        media_type="video/mp4",
        headers=headers,
    )
