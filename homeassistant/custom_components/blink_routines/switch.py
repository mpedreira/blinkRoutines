"""Switch entity: arm/disarm a Blink network."""
from __future__ import annotations

import logging

import aiohttp
from homeassistant.components.switch import SwitchEntity
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
    """Set up the Blink network arm/disarm switch."""
    coordinator: BlinkRoutinesCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([BlinkNetworkSwitch(coordinator)])


class BlinkNetworkSwitch(CoordinatorEntity[BlinkRoutinesCoordinator], SwitchEntity):
    """Switch to arm/disarm a Blink network."""

    _attr_icon = "mdi:shield-home"

    def __init__(self, coordinator: BlinkRoutinesCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_{coordinator.network_id}_switch"
        self._attr_name = (
            f"Blink {coordinator.data.get('network_name', coordinator.network_id)}"
        )

    @property
    def is_on(self) -> bool:
        """Return True when the network is armed."""
        return bool(self.coordinator.data.get("armed"))

    async def async_turn_on(self, **kwargs) -> None:
        """Arm the network."""
        await self._call_api("arm")

    async def async_turn_off(self, **kwargs) -> None:
        """Disarm the network."""
        await self._call_api("disarm")

    async def _call_api(self, action: str) -> None:
        url = f"{self.coordinator.api_url}/api/v1/{action}/{self.coordinator.network_id}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, timeout=aiohttp.ClientTimeout(total=15)
                ) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    if not data.get("is_ok"):
                        _LOGGER.warning(
                            "Blink %s on network %s returned is_ok=False: %s",
                            action,
                            self.coordinator.network_id,
                            data,
                        )
        except aiohttp.ClientError as err:
            _LOGGER.error(
                "Error calling %s on network %s: %s",
                action,
                self.coordinator.network_id,
                err,
            )
        await self.coordinator.async_request_refresh()
