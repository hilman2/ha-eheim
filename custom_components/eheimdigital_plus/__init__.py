# Adapted from Home Assistant Core for ha-eheim. See NOTICE.
"""The EHEIM Digital integration."""

from typing import TYPE_CHECKING

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import AnyDeviceEntry

from ._vendor.eheimdigital.device import EheimDigitalDevice
from .const import DOMAIN
from .coordinator import EheimDigitalConfigEntry, EheimDigitalUpdateCoordinator
from .entity import async_device_info
from .migration import async_migrate_legacy_entry

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.CLIMATE,
    Platform.LIGHT,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.TIME,
]


async def async_setup_entry(
    hass: HomeAssistant, entry: EheimDigitalConfigEntry
) -> bool:
    """Set up EHEIM Digital from a config entry."""

    coordinator = EheimDigitalUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    try:
        async_migrate_legacy_entry(hass, entry)

        main = coordinator.hub.main
        if TYPE_CHECKING:
            # After the first refresh at least one device is found and so there is
            # always a main device set.
            assert isinstance(main, EheimDigitalDevice)
        # Register the main device up front so child devices can resolve their
        # via_device_id link during concurrent platform setup.
        dr.async_get(hass).async_get_or_create(
            config_entry_id=entry.entry_id, **async_device_info(coordinator, main)
        )

        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        coordinator.known_devices.update(
            address
            for address, device in coordinator.hub.devices.items()
            if not device.is_missing_data
        )
    except Exception:
        await coordinator.hub.close()
        raise

    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: EheimDigitalConfigEntry
) -> bool:
    """Unload a config entry."""
    if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        return False
    await entry.runtime_data.hub.close()
    return True


async def async_remove_config_entry_device(
    hass: HomeAssistant,
    config_entry: EheimDigitalConfigEntry,
    device_entry: AnyDeviceEntry,
) -> bool:
    """Remove a config entry from a device."""
    coordinator = config_entry.runtime_data
    for domain, address in device_entry.identifiers:
        if domain != DOMAIN or address not in coordinator.hub.devices:
            continue
        if coordinator.is_device_available(address) or (
            coordinator.hub.main is not None
            and address == coordinator.hub.main.mac_address
        ):
            return False
        coordinator.hub.devices.pop(address)
        coordinator.known_devices.discard(address)
        coordinator.incomplete_devices.discard(address)
        coordinator.device_last_seen.pop(address, None)
    return True
