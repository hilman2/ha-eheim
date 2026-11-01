# Adapted from Home Assistant Core for ha-eheim. See NOTICE.
"""Diagnostics for the EHEIM Digital integration."""

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant

from .coordinator import EheimDigitalConfigEntry

TO_REDACT = {
    CONF_HOST,
    "emailAddr",
    "usrName",
    "api_usrName",
    "api_password",
    "password",
    "ssid",
    "psk",
    "wifi_password",
    "stSSID",
    "stPW",
    "apPW",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: EheimDigitalConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    return async_redact_data(
        {
            "entry": entry.as_dict(),
            "data": {
                address: device.as_dict()
                for address, device in entry.runtime_data.hub.devices.items()
            },
        },
        TO_REDACT,
    )
