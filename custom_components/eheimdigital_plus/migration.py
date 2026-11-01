"""Move an explicitly selected, disabled legacy entry to EHEIM Digital Plus."""

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .const import CONF_MIGRATE_FROM, DOMAIN, LEGACY_DOMAIN
from .coordinator import EheimDigitalConfigEntry


@callback
def async_migrate_legacy_entry(
    hass: HomeAssistant, entry: EheimDigitalConfigEntry
) -> None:
    """Preserve device and entity IDs after the user confirms the migration."""
    if (legacy_id := entry.data.get(CONF_MIGRATE_FROM)) is None:
        return
    legacy = hass.config_entries.async_get_entry(legacy_id)
    if legacy is not None:
        if (
            legacy.domain != LEGACY_DOMAIN
            or legacy.unique_id != entry.unique_id
            or legacy.disabled_by is None
            or legacy.state is not ConfigEntryState.NOT_LOADED
        ):
            raise ConfigEntryNotReady(
                translation_domain=DOMAIN, translation_key="legacy_active"
            )
        device_registry = dr.async_get(hass)
        entity_registry = er.async_get(hass)
        entities = er.async_entries_for_config_entry(entity_registry, legacy_id)
        # Moving a device removes entities still owned by its previous entry.
        # Transfer the entities first, then restore their device links after the move.
        for entity in entities:
            entity_registry.async_update_entity_platform(
                entity.entity_id,
                DOMAIN,
                new_config_entry_id=entry.entry_id,
                new_device_id=None,
            )
        for device in dr.async_entries_for_config_entry(device_registry, legacy_id):
            device_registry.async_update_device(
                device.id,
                new_config_entry_id=entry.entry_id,
                new_identifiers={
                    (DOMAIN if domain == LEGACY_DOMAIN else domain, identifier)
                    for domain, identifier in device.identifiers
                },
            )
        for entity in entities:
            entity_registry.async_update_entity(
                entity.entity_id, device_id=entity.device_id
            )
    hass.config_entries.async_update_entry(
        entry,
        data={
            key: value for key, value in entry.data.items() if key != CONF_MIGRATE_FROM
        },
    )
