"""Exercise connection recovery, silent mesh members and entity lifecycle."""

import logging
from unittest.mock import MagicMock, patch

import pytest
from aiohttp import ClientError
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.eheimdigital_plus import (
    async_remove_config_entry_device,
    async_unload_entry,
)
from custom_components.eheimdigital_plus._vendor.eheimdigital.types import (
    EheimDigitalClientError,
    MsgTitle,
)
from custom_components.eheimdigital_plus.const import DOMAIN
from custom_components.eheimdigital_plus.coordinator import DEVICE_STALE_SECONDS

from .conftest import init_integration

SENSOR = "sensor.mock_aquarium_mock_filter_current_speed"
FILTER = "00:00:00:00:00:04"


async def test_disconnect_and_recovery(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    eheimdigital_hub_mock: MagicMock,
) -> None:
    """A closed connection becomes unavailable immediately and recovers on a packet."""
    await init_integration(hass, mock_config_entry)
    assert hass.states.get(SENSOR).state != "unavailable"
    await eheimdigital_hub_mock.call_args.kwargs["disconnect_callback"]()
    assert hass.states.get(SENSOR).state == "unavailable"
    await eheimdigital_hub_mock.call_args.kwargs["receive_callback"](
        FILTER, MsgTitle.FILTER_DATA
    )
    assert hass.states.get(SENSOR).state != "unavailable"


async def test_outage_is_logged_once(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    eheimdigital_hub_mock: MagicMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Log each outage and recovery once instead of repeating it for every packet."""
    await init_integration(hass, mock_config_entry)
    with caplog.at_level(logging.INFO, logger="custom_components.eheimdigital_plus"):
        caplog.clear()
        disconnected = eheimdigital_hub_mock.call_args.kwargs["disconnect_callback"]
        received = eheimdigital_hub_mock.call_args.kwargs["receive_callback"]
        await disconnected()
        await disconnected()
        await received(FILTER, MsgTitle.FILTER_DATA)
        await received(FILTER, MsgTitle.FILTER_DATA)
    assert caplog.text.count("Error requesting eheimdigital_plus data") == 1
    assert caplog.text.count("Connection to EHEIM Digital recovered") == 1


@pytest.mark.parametrize(
    "error",
    [ClientError("offline"), EheimDigitalClientError("offline"), TimeoutError()],
)
async def test_failed_refresh(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    eheimdigital_hub_mock: MagicMock,
    error: Exception,
) -> None:
    """Transport errors consistently mark entities unavailable instead of leaving stale states."""
    await init_integration(hass, mock_config_entry)
    eheimdigital_hub_mock.return_value.update.side_effect = error
    await mock_config_entry.runtime_data.async_refresh()
    assert hass.states.get(SENSOR).state == "unavailable"
    eheimdigital_hub_mock.return_value.update.side_effect = None
    await eheimdigital_hub_mock.call_args.kwargs["receive_callback"](
        FILTER, MsgTitle.FILTER_DATA
    )
    assert hass.states.get(SENSOR).state != "unavailable"


async def test_connection_failure_closes_hub(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    eheimdigital_hub_mock: MagicMock,
) -> None:
    """A failed initial connection can retry without keeping an old receiver alive."""
    eheimdigital_hub_mock.return_value.connect.side_effect = ClientError("offline")
    await init_integration(hass, mock_config_entry)
    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY
    eheimdigital_hub_mock.return_value.close.assert_awaited_once()


async def test_failed_unload_keeps_connection(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    eheimdigital_hub_mock: MagicMock,
) -> None:
    """The transport stays open when a platform refuses to unload."""
    await init_integration(hass, mock_config_entry)
    with patch(
        "homeassistant.config_entries.ConfigEntries.async_unload_platforms",
        return_value=False,
    ):
        assert not await async_unload_entry(hass, mock_config_entry)
    eheimdigital_hub_mock.return_value.close.assert_not_awaited()


async def test_successful_unload_closes_hub(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    eheimdigital_hub_mock: MagicMock,
) -> None:
    """A real unload removes the entities and closes its WebSocket."""
    await init_integration(hass, mock_config_entry)
    coordinator = mock_config_entry.runtime_data
    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    assert not coordinator.platform_callbacks
    assert hass.states.get(SENSOR).state == "unavailable"
    eheimdigital_hub_mock.return_value.close.assert_awaited_once()


async def test_silent_mesh_member_can_be_removed(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    eheimdigital_hub_mock: MagicMock,
    device_registry: dr.DeviceRegistry,
) -> None:
    """A silent member is unavailable and can be deleted without a reload."""
    await init_integration(hass, mock_config_entry)
    coordinator = mock_config_entry.runtime_data
    coordinator.device_last_seen[FILTER] = hass.loop.time() - DEVICE_STALE_SECONDS - 1
    await eheimdigital_hub_mock.call_args.kwargs["receive_callback"](
        "00:00:00:00:00:01", MsgTitle.USRDTA
    )
    assert hass.states.get(SENSOR).state == "unavailable"
    device = device_registry.async_get_device_by_identifier(
        (DOMAIN, FILTER), mock_config_entry.entry_id
    )
    assert await async_remove_config_entry_device(hass, mock_config_entry, device)
    assert FILTER not in coordinator.hub.devices
    assert FILTER not in coordinator.known_devices


async def test_live_mesh_member_cannot_be_removed(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    eheimdigital_hub_mock: MagicMock,
    device_registry: dr.DeviceRegistry,
) -> None:
    """A working member keeps its entities when removal is requested."""
    await init_integration(hass, mock_config_entry)
    device = device_registry.async_get_device_by_identifier(
        (DOMAIN, FILTER), mock_config_entry.entry_id
    )
    assert not await async_remove_config_entry_device(hass, mock_config_entry, device)


async def test_repeated_announcement_does_not_duplicate_entities(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    eheimdigital_hub_mock: MagicMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """An already registered filter is not added to every platform again."""
    await init_integration(hass, mock_config_entry)
    caplog.clear()
    device = eheimdigital_hub_mock.return_value.devices[FILTER]
    await eheimdigital_hub_mock.call_args.kwargs["device_found_callback"](
        FILTER, device.device_type
    )
    await hass.async_block_till_done()
    assert "already exists" not in caplog.text


async def test_platform_setup_failure_closes_hub(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    eheimdigital_hub_mock: MagicMock,
) -> None:
    """Cleanup also runs if HA rejects forwarding a platform after connecting."""
    with patch(
        "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups",
        side_effect=RuntimeError("platform failed"),
    ):
        await init_integration(hass, mock_config_entry)
    assert mock_config_entry.state is ConfigEntryState.SETUP_ERROR
    eheimdigital_hub_mock.return_value.close.assert_awaited_once()


async def test_silent_main_device_cannot_be_removed(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    eheimdigital_hub_mock: MagicMock,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Removing the main device requires removing the integration entry itself."""
    await init_integration(hass, mock_config_entry)
    coordinator = mock_config_entry.runtime_data
    address = coordinator.hub.main.mac_address
    coordinator.device_last_seen[address] = hass.loop.time() - DEVICE_STALE_SECONDS - 1
    device = device_registry.async_get_device_by_identifier(
        (DOMAIN, address), mock_config_entry.entry_id
    )
    assert not await async_remove_config_entry_device(hass, mock_config_entry, device)


async def test_incomplete_member_waits_for_data(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    eheimdigital_hub_mock: MagicMock,
) -> None:
    """An incomplete mesh member remains unavailable while other devices keep updating."""
    await init_integration(hass, mock_config_entry)
    coordinator = mock_config_entry.runtime_data
    address = "00:00:00:00:00:02"
    heater = coordinator.hub.devices[address]
    packet = heater.heater_data
    heater.heater_data = None
    await eheimdigital_hub_mock.call_args.kwargs["device_found_callback"](
        address, heater.device_type
    )
    await eheimdigital_hub_mock.call_args.kwargs["receive_callback"](
        FILTER, MsgTitle.FILTER_DATA
    )
    assert address in coordinator.incomplete_devices
    assert hass.states.get("climate.mock_aquarium_mock_heater").state == "unavailable"
    heater.heater_data = packet
    await eheimdigital_hub_mock.call_args.kwargs["receive_callback"](
        address, MsgTitle.HEATER_DATA
    )
    assert address not in coordinator.incomplete_devices
    assert hass.states.get("climate.mock_aquarium_mock_heater").state != "unavailable"
