"""Verify behavior specific to the packaged Core replacement."""

import json
from unittest.mock import MagicMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.loader import async_get_integration
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.eheimdigital_plus.const import DOMAIN
from custom_components.eheimdigital_plus.diagnostics import (
    async_get_config_entry_diagnostics,
)

from .conftest import init_integration


async def test_existing_registry_entry_is_reused(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    eheimdigital_hub_mock: MagicMock,
    entity_registry: er.EntityRegistry,
) -> None:
    """An installed replacement must preserve existing automation targets."""
    entity_registry.async_get_or_create(
        "sensor",
        DOMAIN,
        "00:00:00:00:00:04_current_speed",
        suggested_object_id="existing_filter_speed",
    )
    await init_integration(hass, mock_config_entry)
    integration = await async_get_integration(hass, DOMAIN)
    assert not integration.is_built_in
    assert hass.states.get("sensor.existing_filter_speed") is not None
    assert hass.states.get("sensor.existing_filter_speed_2") is None


async def test_diagnostics_redacts_device_credentials(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    eheimdigital_hub_mock: MagicMock,
) -> None:
    """Serialize device objects before recursively redacting their credentials."""
    await init_integration(hass, mock_config_entry)
    device = eheimdigital_hub_mock.return_value.main
    device.usrdta["api_password"] = "diagnostic-secret-marker"
    device.usrdta["ssid"] = "private-network-marker"
    result = await async_get_config_entry_diagnostics(hass, mock_config_entry)
    serialized = json.dumps(
        result,
        default=lambda value: (
            value.as_dict() if hasattr(value, "as_dict") else str(value)
        ),
    )
    assert "diagnostic-secret-marker" not in serialized
    assert "private-network-marker" not in serialized
    assert (
        result["data"][device.mac_address]["usrdta"]["api_password"] == "**REDACTED**"
    )
    assert device.usrdta["api_password"] == "diagnostic-secret-marker"


@pytest.mark.parametrize("error", [TimeoutError(), ConnectionError()])
async def test_config_flow_closes_connection_on_failure(
    hass: HomeAssistant, eheimdigital_hub_mock: MagicMock, error: Exception
) -> None:
    """A failed configuration attempt must not leave a receiver connected."""
    eheimdigital_hub_mock.return_value.connect.side_effect = error
    flow = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}, data={"host": "eheimdigital"}
    )
    assert flow["type"] == "form"
    eheimdigital_hub_mock.return_value.close.assert_awaited_once()
