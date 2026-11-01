"""Verify an optional control stays disabled until a user enables it."""

from unittest.mock import MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.eheimdigital_plus.const import DOMAIN

from .conftest import init_integration, mock_event


@pytest.mark.parametrize("address", [f"00:00:00:00:00:0{i}" for i in range(1, 6)])
async def test_optional_system_led(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    eheimdigital_hub_mock: MagicMock,
    entity_registry: er.EntityRegistry,
    address: str,
) -> None:
    """Enable the LED control, reload, and exercise both writes and state updates."""
    await init_integration(hass, mock_config_entry)
    entity_id = entity_registry.async_get_entity_id(
        "number", DOMAIN, f"{address}_system_led"
    )
    entity = entity_registry.async_get(entity_id)
    assert entity.disabled_by is er.RegistryEntryDisabler.INTEGRATION
    assert hass.states.get(entity_id) is None
    entity_registry.async_update_entity(entity_id, disabled_by=None)
    with patch(
        "custom_components.eheimdigital_plus.coordinator.asyncio.Event", new=mock_event
    ):
        assert await hass.config_entries.async_reload(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    await hass.services.async_call(
        "number", "set_value", {"entity_id": entity_id, "value": 23}, blocking=True
    )
    assert (
        eheimdigital_hub_mock.return_value.devices[
            address
        ].hub.send_packet.call_args.args[0]["sysLED"]
        == 23
    )
    eheimdigital_hub_mock.return_value.devices[address].usrdta["sysLED"] = 23
    await eheimdigital_hub_mock.call_args.kwargs["receive_callback"]()
    assert float(hass.states.get(entity_id).state) == 23
