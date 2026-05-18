"""DataUpdateCoordinator for Blink Routines."""
from __future__ import annotations

import json
import logging
from datetime import timedelta

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

import os

from .const import (
    CONF_API_URL,
    CONF_NETWORK_ID,
    CONF_SCAN_INTERVAL,
    CONF_TELEGRAM_CHANNEL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_DEVICES_PATH = os.path.join(os.path.dirname(__file__), "blink_devices.json")

_LOGGER = logging.getLogger(__name__)


class BlinkRoutinesCoordinator(DataUpdateCoordinator[dict]):
    """Coordinator that polls the blinkRoutines API and reads devices from JSON."""

    _FAILURE_TOLERANCE = 3  # raise UpdateFailed only after this many consecutive errors

    def __init__(self, hass: HomeAssistant, config_entry) -> None:
        self.api_url: str = config_entry.data[CONF_API_URL].rstrip("/")
        self.network_id: str = config_entry.data[CONF_NETWORK_ID]
        self.telegram_channel: str = config_entry.data[CONF_TELEGRAM_CHANNEL]
        self.cameras: list[dict] = []
        self._consecutive_failures: int = 0
        interval_minutes: int = config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=interval_minutes),
        )

    def _load_cameras(self) -> list[dict]:
        """Load camera list from blink_devices.json (blocking I/O)."""
        with open(_DEVICES_PATH, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("cameras", [])

    async def _async_update_data(self) -> dict:
        """Fetch latest network status from the blinkRoutines API."""
        if not self.cameras:
            try:
                self.cameras = await self.hass.async_add_executor_job(self._load_cameras)
            except (OSError, json.JSONDecodeError) as err:
                raise UpdateFailed(f"Error reading blink_devices.json: {err}") from err

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_url}/api/v1/network_status/{self.network_id}",
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    resp.raise_for_status()
                    payload: dict = await resp.json()
        except (aiohttp.ClientError, TimeoutError) as err:
            self._consecutive_failures += 1
            if self.data is not None and self._consecutive_failures < self._FAILURE_TOLERANCE:
                _LOGGER.warning(
                    "blinkRoutines API unreachable (attempt %d/%d), returning cached data: %s",
                    self._consecutive_failures,
                    self._FAILURE_TOLERANCE,
                    err,
                )
                return self.data
            raise UpdateFailed(
                f"Error communicating with blinkRoutines API: {err}"
            ) from err

        self._consecutive_failures = 0

        return {
            "armed": bool(payload.get("enabled")),
            "network_name": payload.get("name", f"Red {self.network_id}"),
            "cameras": self.cameras,
        }
