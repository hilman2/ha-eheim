"""Verify the user-confirmed migration across integration domains."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryDisabler
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.eheimdigital_plus.const import (
    CONF_MIGRATE_FROM,
    DOMAIN,
    LEGACY_DOMAIN,
)
from custom_components.eheimdigital_plus.migration import async_migrate_legacy_entry

from .conftest import init_integration, mock_event
from .test_config_flow import USER_INPUT, ZEROCONF_DISCOVERY


@pytest.fixture
def legacy_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Return a disabled legacy setup for the same verified main device."""
    entry = MockConfigEntry(
        domain=LEGACY_DOMAIN,
        data=USER_INPUT,
        unique_id="00:00:00:00:00:01",
        disabled_by=ConfigEntryDisabler.USER,
    )
    entry.add_to_hass(hass)
    return entry


@pytest.mark.parametrize(
    "disabled_by",
    [None, er.RegistryEntryDisabler.USER, er.RegistryEntryDisabler.CONFIG_ENTRY],
)
async def test_preserve_entity_and_device_ids(
    hass: HomeAssistant,
    legacy_entry: MockConfigEntry,
    mock_config_entry: MockConfigEntry,
    eheimdigital_hub_mock: MagicMock,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
    disabled_by: er.RegistryEntryDisabler | None,
) -> None:
    """A confirmed migration preserves IDs, custom names and user choices."""
    device = device_registry.async_get_or_create(
        config_entry_id=legacy_entry.entry_id,
        identifiers={(LEGACY_DOMAIN, "00:00:00:00:00:04")},
        name="Existing filter",
    )
    entity = entity_registry.async_get_or_create(
        "sensor",
        LEGACY_DOMAIN,
        "00:00:00:00:00:04_current_speed",
        config_entry=legacy_entry,
        device_id=device.id,
        suggested_object_id="existing_filter_speed",
        disabled_by=disabled_by,
    )
    entity_registry.async_update_entity(entity.entity_id, name="My filter speed")
    mock_config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=mock_config_entry.unique_id,
        data={**USER_INPUT, CONF_MIGRATE_FROM: legacy_entry.entry_id},
    )
    await init_integration(hass, mock_config_entry)
    migrated = entity_registry.async_get(entity.entity_id)
    assert migrated.platform == DOMAIN
    assert migrated.config_entry_id == mock_config_entry.entry_id
    assert migrated.device_id == device.id
    assert migrated.name == "My filter speed"
    assert migrated.disabled_by == (
        er.RegistryEntryDisabler.USER
        if disabled_by is er.RegistryEntryDisabler.USER
        else None
    )
    assert (DOMAIN, "00:00:00:00:00:04") in device_registry.async_get(
        device.id
    ).identifiers
    assert CONF_MIGRATE_FROM not in mock_config_entry.data
    assert legacy_entry.disabled_by is ConfigEntryDisabler.USER


@pytest.mark.parametrize("change", ["enabled", "different_device", "different_domain"])
async def test_refuse_unsafe_migration(
    hass: HomeAssistant,
    legacy_entry: MockConfigEntry,
    mock_config_entry: MockConfigEntry,
    change: str,
) -> None:
    """Do not move registries when the old setup is active or belongs elsewhere."""
    if change == "enabled":
        legacy_entry = MockConfigEntry(
            domain=LEGACY_DOMAIN, unique_id=mock_config_entry.unique_id
        )
        legacy_entry.add_to_hass(hass)
    elif change == "different_device":
        hass.config_entries.async_update_entry(
            legacy_entry, unique_id="00:00:00:00:00:99"
        )
    else:
        legacy_entry = MockConfigEntry(
            domain="other",
            unique_id=mock_config_entry.unique_id,
            disabled_by=ConfigEntryDisabler.USER,
        )
        legacy_entry.add_to_hass(hass)
    mock_config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=mock_config_entry.unique_id,
        data={**USER_INPUT, CONF_MIGRATE_FROM: legacy_entry.entry_id},
    )
    mock_config_entry.add_to_hass(hass)
    with pytest.raises(ConfigEntryNotReady):
        async_migrate_legacy_entry(hass, mock_config_entry)


async def test_deleted_legacy_entry(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """A user who deleted the old entry can still finish the new setup."""
    mock_config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=mock_config_entry.unique_id,
        data={**USER_INPUT, CONF_MIGRATE_FROM: "deleted-entry"},
    )
    mock_config_entry.add_to_hass(hass)
    async_migrate_legacy_entry(hass, mock_config_entry)
    assert mock_config_entry.data == USER_INPUT


@pytest.mark.parametrize("source", ["user", "zeroconf"])
@patch("custom_components.eheimdigital_plus.config_flow.asyncio.Event", new=mock_event)
async def test_confirm_migration(
    hass: HomeAssistant,
    legacy_entry: MockConfigEntry,
    eheimdigital_hub_mock: AsyncMock,
    source: str,
) -> None:
    """Creating the replacement entry requires an explicit migration confirmation."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": source},
        data=USER_INPUT if source == "user" else ZEROCONF_DISCOVERY,
    )
    if source == "zeroconf":
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "migrate"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_MIGRATE_FROM] == legacy_entry.entry_id


@patch("custom_components.eheimdigital_plus.config_flow.asyncio.Event", new=mock_event)
async def test_active_legacy_setup_blocks_flow(
    hass: HomeAssistant, eheimdigital_hub_mock: MagicMock
) -> None:
    """Explain how to disable an existing setup instead of opening two connections."""
    legacy = MockConfigEntry(domain=LEGACY_DOMAIN, unique_id="00:00:00:00:00:01")
    legacy.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}, data=USER_INPUT
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "legacy_active"
