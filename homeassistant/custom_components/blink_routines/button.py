"""Button entities: trigger a thumbnail snapshot per camera."""
from __future__ import annotations

import logging

import aiohttp
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import BlinkRoutinesCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up one snapshot button per camera discovered in blink_devices.json."""
    coordinator: BlinkRoutinesCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        BlinkCameraSnapshotButton(coordinator, cam) for cam in coordinator.cameras
    )


class BlinkCameraSnapshotButton(
    CoordinatorEntity[BlinkRoutinesCoordinator], ButtonEntity
):
    """Button that triggers a new thumbnail capture on a Blink camera."""

    _attr_icon = "mdi:camera"

    def __init__(self, coordinator: BlinkRoutinesCoordinator, camera: dict) -> None:
        super().__init__(coordinator)
        self._cam_name: str = camera["name"]
        self._cam_id: str = str(camera["id"])
        self._cam_type: str = camera.get("type", "cam")
        self._attr_unique_id = f"{DOMAIN}_{self._cam_name.lower()}_snapshot"
        self._attr_name = f"Blink {self._cam_name} – Snapshot"

    async def async_press(self) -> None:
        """Trigger a new thumbnail capture on the camera."""
        endpoint = "update_owl" if self._cam_type == "owl" else "update_thumb"
        url = f"{self.coordinator.api_url}/api/v1/{endpoint}/{self._cam_id}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    if not data.get("is_ok"):
                        _LOGGER.warning(
                            "Snapshot for camera '%s' returned is_ok=False: %s",
                            self._cam_name,
                            data,
                        )
        except aiohttp.ClientError as err:
            _LOGGER.error(
                "Error triggering snapshot for camera '%s': %s",
                self._cam_name,
                err,
            )
