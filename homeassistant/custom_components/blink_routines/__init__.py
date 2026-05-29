"""Blink Routines Home Assistant custom component."""
from __future__ import annotations

import asyncio
import logging

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall

from .const import (
    ATTR_CAM_NAME,
    ATTR_MIN_CONFIDENCE,
    ATTR_PERSON_NAME,
    ATTR_SAMPLE_FPS,
    DOMAIN,
    EVENT_THUMB_FACE_DETECTED,
    EVENT_THUMB_FACE_REGISTERED,
    EVENT_VIDEO_FACE_DETECTED,
    EVENT_VIDEO_FACE_ERROR,
    EVENT_VIDEO_FACE_REGISTERED,
    SERVICE_DETECT_VIDEO_FACES,
    SERVICE_REGISTER_VIDEO_FACE,
)
from .coordinator import BlinkRoutinesCoordinator, _DEVICES_PATH

PLATFORMS = ["switch", "button"]
_SERVICES_REGISTERED_KEY = "_services_registered"
_MODULE_SIGNATURE = "blink_routines_fallback_v6_2026_05_29"

_LOGGER = logging.getLogger(__name__)


def _find_coordinator_for_camera(hass: HomeAssistant, cam_name: str) -> BlinkRoutinesCoordinator | None:
    """Return the coordinator whose network_id matches the camera's network_id in blink_devices.json.

    Falls back to the first loaded coordinator when no match is found so that
    pre-existing automations keep working even if blink_devices.json is outdated.
    """
    import json as _json
    try:
        with open(_DEVICES_PATH, encoding="utf-8") as _f:
            _devices = _json.load(_f)
        camera_network_id = next(
            (c["network_id"] for c in _devices.get("cameras", []) if c.get("name") == cam_name),
            None,
        )
    except (OSError, _json.JSONDecodeError, KeyError):
        camera_network_id = None

    domain_data = hass.data.get(DOMAIN, {})
    first: BlinkRoutinesCoordinator | None = None
    for value in domain_data.values():
        if not isinstance(value, BlinkRoutinesCoordinator):
            continue
        if first is None:
            first = value
        if camera_network_id and value.network_id == camera_network_id:
            return value
    return first


async def _download_video(api_url: str, cam_name: str) -> bytes:
    """Download the latest local clip from the main blinkRoutines API."""
    video_url = f"{api_url}/api/v2/get_local_video/{cam_name}"
    async with aiohttp.ClientSession() as session:
        async with session.get(
            video_url,
            timeout=aiohttp.ClientTimeout(total=90),
        ) as response:
            response.raise_for_status()
            return await response.read()


async def _download_image(api_url: str, cam_name: str) -> bytes:
    """Download current camera thumbnail from the main blinkRoutines API."""
    image_url = f"{api_url}/api/v2/get_thumb_image/{cam_name}"
    async with aiohttp.ClientSession() as session:
        async with session.get(
            image_url,
            timeout=aiohttp.ClientTimeout(total=60),
        ) as response:
            response.raise_for_status()
            return await response.read()


async def _fetch_network_enabled(api_url: str, network_id: str) -> bool:
    """Fetch network status from API and return enabled flag as strict bool."""
    status_url = f"{api_url}/api/v1/network_status/{network_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(
            status_url,
            timeout=aiohttp.ClientTimeout(total=10),
        ) as response:
            response.raise_for_status()
            payload = await response.json()
    return payload.get("enabled") is True


async def _get_capture_bytes(
    api_url: str,
    network_id: str,
    cam_name: str,
    wait_seconds: int,
) -> tuple[bytes, str]:
    """Capture video when network is enabled, otherwise capture a thumbnail image."""
    is_enabled = await _fetch_network_enabled(api_url, network_id)
    if is_enabled:
        if wait_seconds > 0:
            await asyncio.sleep(wait_seconds)
        try:
            return await _download_video(api_url, cam_name), "video"
        except Exception as err:  # fallback must trigger on any video retrieval failure
            _LOGGER.info(
                "Video download failed for camera '%s' (%s); falling back to thumbnail",
                cam_name,
                err,
            )
            return await _download_image(api_url, cam_name), "thumbnail"

    return await _download_image(api_url, cam_name), "thumbnail"


async def _post_video(
    base_url: str,
    endpoint: str,
    video: bytes,
    sample_fps: float,
    min_confidence: float | None = None,
) -> dict:
    """Post a video payload to agents API and parse JSON response."""
    form_data = aiohttp.FormData()
    form_data.add_field("video", video, filename="camera.mp4", content_type="video/mp4")
    form_data.add_field(ATTR_SAMPLE_FPS, str(sample_fps))
    if min_confidence is not None:
        form_data.add_field(ATTR_MIN_CONFIDENCE, str(min_confidence))

    agents_url = f"{base_url}{endpoint}"
    async with aiohttp.ClientSession() as session:
        async with session.post(
            agents_url,
            data=form_data,
            timeout=aiohttp.ClientTimeout(total=240),
        ) as response:
            response.raise_for_status()
            return await response.json()


async def _post_image(
    base_url: str,
    endpoint: str,
    image: bytes,
    min_confidence: float | None = None,
) -> dict:
    """Post an image payload to agents API and parse JSON response."""
    form_data = aiohttp.FormData()
    form_data.add_field("image", image, filename="camera.jpg", content_type="image/jpeg")
    if min_confidence is not None:
        form_data.add_field(ATTR_MIN_CONFIDENCE, str(min_confidence))

    agents_url = f"{base_url}{endpoint}"
    async with aiohttp.ClientSession() as session:
        async with session.post(
            agents_url,
            data=form_data,
            timeout=aiohttp.ClientTimeout(total=120),
        ) as response:
            response.raise_for_status()
            return await response.json()


async def _handle_detect_video_faces(hass: HomeAssistant, call: ServiceCall) -> None:
    """Download latest camera clip and run detection against agents API."""
    _LOGGER.warning("[%s] detect_video_faces called", _MODULE_SIGNATURE)
    cam_name = call.data[ATTR_CAM_NAME]
    coordinator = _find_coordinator_for_camera(hass, cam_name)
    if coordinator is None:
        _LOGGER.error("No coordinator loaded for %s service", SERVICE_DETECT_VIDEO_FACES)
        return

    _LOGGER.warning("[%s] detect_video_faces cam=%s network=%s agents=%s", _MODULE_SIGNATURE, cam_name, coordinator.network_id, coordinator.agents_api_url)
    sample_fps = float(call.data.get(ATTR_SAMPLE_FPS, 1.0))
    min_confidence = float(call.data.get(ATTR_MIN_CONFIDENCE, coordinator.min_confidence))
    source = "thumbnail"  # default; updated after successful capture

    try:
        _LOGGER.warning("[%s] calling _get_capture_bytes", _MODULE_SIGNATURE)
        capture_bytes, source = await _get_capture_bytes(
            coordinator.api_url,
            coordinator.network_id,
            cam_name,
            max(0, int(coordinator.last_video_wait_seconds)),
        )
        _LOGGER.warning("[%s] capture done source=%s bytes=%d", _MODULE_SIGNATURE, source, len(capture_bytes))
        if source == "video":
            payload = await _post_video(
                coordinator.agents_api_url,
                "/api/v2/detect_person",
                capture_bytes,
                sample_fps,
                min_confidence=min_confidence,
            )
            _LOGGER.warning("[%s] agents video response=%s", _MODULE_SIGNATURE, payload)
            hass.bus.async_fire(
                EVENT_VIDEO_FACE_DETECTED,
                {
                    ATTR_CAM_NAME: cam_name,
                    "source": source,
                    "result": payload.get("response", {}),
                },
            )
        else:
            payload = await _post_image(
                coordinator.agents_api_url,
                "/api/v2/detect_person_image",
                capture_bytes,
                min_confidence=min_confidence,
            )
            _LOGGER.warning("[%s] agents image response=%s", _MODULE_SIGNATURE, payload)
            hass.bus.async_fire(
                EVENT_THUMB_FACE_DETECTED,
                {
                    ATTR_CAM_NAME: cam_name,
                    "source": source,
                    "result": payload.get("response", {}),
                },
            )
        _LOGGER.warning("[%s] event fired OK", _MODULE_SIGNATURE)
    except (aiohttp.ClientError, TimeoutError, ValueError) as err:
        _LOGGER.warning("[%s] ClientError/Timeout/ValueError: %s", _MODULE_SIGNATURE, err)
        # Last-chance fallback: if anything in the video path leaked, retry with image.
        try:
            image = await _download_image(coordinator.api_url, cam_name)
            payload = await _post_image(
                coordinator.agents_api_url,
                "/api/v2/detect_person_image",
                image,
                min_confidence=min_confidence,
            )
            hass.bus.async_fire(
                EVENT_THUMB_FACE_DETECTED,
                {
                    ATTR_CAM_NAME: cam_name,
                    "source": "thumbnail",
                    "result": payload.get("response", {}),
                },
            )
            return
        except (aiohttp.ClientError, TimeoutError, ValueError) as image_err:
            _LOGGER.error(
                "detect_video_faces failed for %s (video and image fallback): %s",
                cam_name,
                image_err,
            )
            hass.bus.async_fire(
                EVENT_VIDEO_FACE_ERROR,
                {
                    "service": SERVICE_DETECT_VIDEO_FACES,
                    ATTR_CAM_NAME: cam_name,
                    "source": source,
                    "error": f"[{_MODULE_SIGNATURE}] {image_err}",
                },
            )


async def _handle_register_video_face(hass: HomeAssistant, call: ServiceCall) -> None:
    """Download latest camera clip and register the face in agents API."""
    coordinator = _find_coordinator_for_camera(hass, call.data[ATTR_CAM_NAME])
    if coordinator is None:
        _LOGGER.error("No coordinator loaded for %s service", SERVICE_REGISTER_VIDEO_FACE)
        return

    cam_name = call.data[ATTR_CAM_NAME]
    person_name = call.data[ATTR_PERSON_NAME]
    sample_fps = float(call.data.get(ATTR_SAMPLE_FPS, 1.0))
    source = "thumbnail"  # default; updated after successful capture

    try:
        capture_bytes, source = await _get_capture_bytes(
            coordinator.api_url,
            coordinator.network_id,
            cam_name,
            max(0, int(coordinator.last_video_wait_seconds)),
        )
        if source == "video":
            payload = await _post_video(
                coordinator.agents_api_url,
                f"/api/v2/register_face/{person_name}",
                capture_bytes,
                sample_fps,
            )
            hass.bus.async_fire(
                EVENT_VIDEO_FACE_REGISTERED,
                {
                    ATTR_CAM_NAME: cam_name,
                    ATTR_PERSON_NAME: person_name,
                    "source": source,
                    "result": payload.get("response", {}),
                },
            )
        else:
            payload = await _post_image(
                coordinator.agents_api_url,
                f"/api/v2/register_face_image/{person_name}",
                capture_bytes,
            )
            hass.bus.async_fire(
                EVENT_THUMB_FACE_REGISTERED,
                {
                    ATTR_CAM_NAME: cam_name,
                    ATTR_PERSON_NAME: person_name,
                    "source": source,
                    "result": payload.get("response", {}),
                },
            )
    except (aiohttp.ClientError, TimeoutError, ValueError) as err:
        # Last-chance fallback: if anything in the video path leaked, retry register via image.
        try:
            image = await _download_image(coordinator.api_url, cam_name)
            payload = await _post_image(
                coordinator.agents_api_url,
                f"/api/v2/register_face_image/{person_name}",
                image,
            )
            hass.bus.async_fire(
                EVENT_THUMB_FACE_REGISTERED,
                {
                    ATTR_CAM_NAME: cam_name,
                    ATTR_PERSON_NAME: person_name,
                    "source": "thumbnail",
                    "result": payload.get("response", {}),
                },
            )
            return
        except (aiohttp.ClientError, TimeoutError, ValueError) as image_err:
            _LOGGER.error(
                "register_video_face failed for %s (video and image fallback): %s",
                cam_name,
                image_err,
            )
            hass.bus.async_fire(
                EVENT_VIDEO_FACE_ERROR,
                {
                    "service": SERVICE_REGISTER_VIDEO_FACE,
                    ATTR_CAM_NAME: cam_name,
                    ATTR_PERSON_NAME: person_name,
                    "source": source,
                    "error": f"[{_MODULE_SIGNATURE}] {image_err}",
                },
            )


def _register_services(hass: HomeAssistant) -> None:
    """Register custom services once."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    if domain_data.get(_SERVICES_REGISTERED_KEY):
        return

    async def _detect_service(call: ServiceCall) -> None:
        await _handle_detect_video_faces(hass, call)

    async def _register_service(call: ServiceCall) -> None:
        await _handle_register_video_face(hass, call)

    hass.services.async_register(
        DOMAIN,
        SERVICE_DETECT_VIDEO_FACES,
        _detect_service,
        schema=vol.Schema(
            {
                vol.Required(ATTR_CAM_NAME): str,
                vol.Optional(ATTR_SAMPLE_FPS, default=1.0): vol.Coerce(float),
                vol.Optional(ATTR_MIN_CONFIDENCE, default=70.0): vol.Coerce(float),
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_REGISTER_VIDEO_FACE,
        _register_service,
        schema=vol.Schema(
            {
                vol.Required(ATTR_CAM_NAME): str,
                vol.Required(ATTR_PERSON_NAME): str,
                vol.Optional(ATTR_SAMPLE_FPS, default=1.0): vol.Coerce(float),
            }
        ),
    )
    domain_data[_SERVICES_REGISTERED_KEY] = True


def _unregister_services_if_unused(hass: HomeAssistant) -> None:
    """Unregister services once there are no loaded coordinators."""
    domain_data = hass.data.get(DOMAIN, {})
    still_loaded = any(
        isinstance(value, BlinkRoutinesCoordinator)
        for value in domain_data.values()
    )
    if still_loaded:
        return

    hass.services.async_remove(DOMAIN, SERVICE_DETECT_VIDEO_FACES)
    hass.services.async_remove(DOMAIN, SERVICE_REGISTER_VIDEO_FACE)
    domain_data[_SERVICES_REGISTERED_KEY] = False


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Blink Routines from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    _LOGGER.warning("Loaded %s", _MODULE_SIGNATURE)

    coordinator = BlinkRoutinesCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator
    _register_services(hass)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        _unregister_services_if_unused(hass)
    return unload_ok
