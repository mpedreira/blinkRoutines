"""Config flow for Blink Routines."""
from __future__ import annotations

from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_API_URL,
    CONF_NETWORK_ID,
    CONF_SCAN_INTERVAL,
    CONF_TELEGRAM_CHANNEL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

STEP_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_URL): str,
        vol.Required(CONF_NETWORK_ID): str,
        vol.Required(CONF_TELEGRAM_CHANNEL): str,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
            vol.Coerce(int), vol.Range(min=1)
        ),
    }
)


async def _validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, str]:
    """Validate user input. Returns a dict of field → error key (empty = OK)."""
    errors: dict[str, str] = {}

    # Validate API connectivity
    api_url = data[CONF_API_URL].rstrip("/")
    network_id = data[CONF_NETWORK_ID]
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{api_url}/api/v1/network_status/{network_id}",
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status >= 500:
                    errors[CONF_API_URL] = "cannot_connect"
    except (aiohttp.ClientError, TimeoutError):
        errors[CONF_API_URL] = "cannot_connect"

    return errors


class BlinkRoutinesConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Blink Routines."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api_url = user_input[CONF_API_URL].rstrip("/")
            network_id = user_input[CONF_NETWORK_ID]

            await self.async_set_unique_id(f"{api_url}_{network_id}")
            self._abort_if_unique_id_configured()

            errors = await _validate_input(self.hass, {**user_input, CONF_API_URL: api_url})
            if not errors:
                return self.async_create_entry(
                    title=f"Blink – Red {network_id}",
                    data={**user_input, CONF_API_URL: api_url},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_SCHEMA,
            errors=errors,
        )
