"""Cover malformed inputs, unsupported devices and rediscovery."""

from unittest.mock import MagicMock, patch

import pytest
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.eheimdigital_plus._vendor.eheimdigital.device import (
    EheimDigitalDevice,
)
from custom_components.eheimdigital_plus.const import DOMAIN, LEGACY_DOMAIN

from .conftest import init_integration, mock_event
from .test_config_flow import USER_INPUT, ZEROCONF_DISCOVERY


@pytest.mark.parametrize(
    "host", ["", "   ", "http://192.0.2.1", "eheimdigital/ws", "192.0.2.1:80"]
)
async def test_invalid_host(
    hass: HomeAssistant, eheimdigital_hub_mock: MagicMock, host: str
) -> None:
    """Give a field error for invalid addresses instead of crashing the flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}, data={CONF_HOST: host}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_host"}


async def test_invalid_address_constructor(
    hass: HomeAssistant, eheimdigital_hub_mock: MagicMock
) -> None:
    """Handle addresses rejected by URL parsing during hub construction."""
    eheimdigital_hub_mock.side_effect = ValueError("invalid host")
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}, data=USER_INPUT
    )
    assert result["errors"] == {"base": "invalid_host"}


@pytest.mark.parametrize("source", ["user", "zeroconf"])
@patch("custom_components.eheimdigital_plus.config_flow.asyncio.Event", new=mock_event)
async def test_unsupported_device(
    hass: HomeAssistant, eheimdigital_hub_mock: MagicMock, source: str
) -> None:
    """Do not create an empty integration for a device without entity support."""
    usrdta = dict(eheimdigital_hub_mock.return_value.main.usrdta, version=3)
    eheimdigital_hub_mock.return_value.main = EheimDigitalDevice(MagicMock(), usrdta)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": source},
        data=USER_INPUT if source == "user" else ZEROCONF_DISCOVERY,
    )
    if source == "user":
        assert result["errors"] == {"base": "unsupported_device"}
    else:
        assert result["reason"] == "unsupported_device"
    eheimdigital_hub_mock.return_value.close.assert_awaited_once()


@patch("custom_components.eheimdigital_plus.config_flow.asyncio.Event", new=mock_event)
async def test_missing_device_identity(
    hass: HomeAssistant, eheimdigital_hub_mock: MagicMock
) -> None:
    """An empty handshake must be recoverable as a connection failure."""
    eheimdigital_hub_mock.return_value.main = None
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}, data=USER_INPUT
    )
    assert result["errors"] == {"base": "cannot_connect"}


async def test_handshake_timeout(
    hass: HomeAssistant, eheimdigital_hub_mock: MagicMock
) -> None:
    """Close the probe when the device never announces itself."""
    event = mock_event()
    event.wait.side_effect = TimeoutError()
    with patch(
        "custom_components.eheimdigital_plus.config_flow.asyncio.Event",
        return_value=event,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}, data=USER_INPUT
        )
    assert result["errors"] == {"base": "cannot_connect"}
    eheimdigital_hub_mock.return_value.close.assert_awaited_once()


@patch("custom_components.eheimdigital_plus.config_flow.asyncio.Event", new=mock_event)
async def test_rediscovery_updates_host(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    eheimdigital_hub_mock: MagicMock,
) -> None:
    """Identify an existing main device by its MAC and refresh its changed address."""
    await init_integration(hass, mock_config_entry)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "zeroconf"}, data=ZEROCONF_DISCOVERY
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert mock_config_entry.data[CONF_HOST] == ZEROCONF_DISCOVERY.host


@patch("custom_components.eheimdigital_plus.config_flow.asyncio.Event", new=mock_event)
async def test_other_legacy_device_is_independent(
    hass: HomeAssistant, eheimdigital_hub_mock: MagicMock
) -> None:
    """A Core entry for another aquarium must not be offered for migration."""
    legacy = MockConfigEntry(domain=LEGACY_DOMAIN, unique_id="different-device")
    legacy.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}, data=USER_INPUT
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == USER_INPUT
