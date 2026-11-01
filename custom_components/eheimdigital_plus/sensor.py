# Adapted from Home Assistant Core for ha-eheim. See NOTICE.
"""EHEIM Digital sensors."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, override

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTime,
    UnitOfVolumeFlowRate,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from ._vendor.eheimdigital.classic_vario import EheimDigitalClassicVario
from ._vendor.eheimdigital.device import EheimDigitalDevice
from ._vendor.eheimdigital.filter import EheimDigitalFilter
from ._vendor.eheimdigital.types import FilterErrorCode, FilterErrorCodeProf
from .coordinator import EheimDigitalConfigEntry, EheimDigitalUpdateCoordinator
from .entity import EheimDigitalEntity

# Coordinator is used to centralize the data updates
PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class EheimDigitalSensorDescription[_DeviceT: EheimDigitalDevice](
    SensorEntityDescription
):
    """Class describing EHEIM Digital sensor entities."""

    value_fn: Callable[[_DeviceT], float | str | None]


FILTER_DESCRIPTIONS: tuple[EheimDigitalSensorDescription[EheimDigitalFilter], ...] = (
    EheimDigitalSensorDescription[EheimDigitalFilter](
        key="current_speed",
        translation_key="current_speed",
        value_fn=lambda device: device.current_speed,
        device_class=SensorDeviceClass.FREQUENCY,
        suggested_display_precision=1,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
    ),
    EheimDigitalSensorDescription[EheimDigitalFilter](
        key="error_code",
        translation_key="error_code",
        value_fn=lambda device: device.error_code.name.lower(),
        device_class=SensorDeviceClass.ENUM,
        options=[name.lower() for name in FilterErrorCodeProf.__members__],
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    EheimDigitalSensorDescription[EheimDigitalFilter](
        key="estimated_flow_rate",
        translation_key="estimated_flow_rate",
        value_fn=lambda device: device.estimated_flow_rate,
        device_class=SensorDeviceClass.VOLUME_FLOW_RATE,
        native_unit_of_measurement=UnitOfVolumeFlowRate.LITERS_PER_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
    EheimDigitalSensorDescription[EheimDigitalFilter](
        key="estimated_power",
        translation_key="estimated_power",
        value_fn=lambda device: device.estimated_power,
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    EheimDigitalSensorDescription[EheimDigitalFilter](
        key="service_hours",
        translation_key="service_hours",
        value_fn=lambda device: device.service_hours,
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.HOURS,
        suggested_unit_of_measurement=UnitOfTime.DAYS,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    EheimDigitalSensorDescription[EheimDigitalFilter](
        key="operating_time",
        translation_key="operating_time",
        value_fn=lambda device: device.operating_time,
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        suggested_unit_of_measurement=UnitOfTime.HOURS,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    EheimDigitalSensorDescription[EheimDigitalFilter](
        key="turn_off_time",
        translation_key="turn_off_time",
        value_fn=lambda device: device.turn_off_time,
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_unit_of_measurement=UnitOfTime.MINUTES,
        suggested_display_precision=2,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    EheimDigitalSensorDescription[EheimDigitalFilter](
        key="turn_feeding_time",
        translation_key="turn_feeding_time",
        value_fn=lambda device: device.turn_feeding_time,
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_unit_of_measurement=UnitOfTime.MINUTES,
        suggested_display_precision=2,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


CLASSICVARIO_DESCRIPTIONS: tuple[
    EheimDigitalSensorDescription[EheimDigitalClassicVario], ...
] = (
    EheimDigitalSensorDescription[EheimDigitalClassicVario](
        key="current_speed",
        translation_key="current_speed",
        value_fn=lambda device: device.current_speed,
        native_unit_of_measurement=PERCENTAGE,
    ),
    EheimDigitalSensorDescription[EheimDigitalClassicVario](
        key="service_hours",
        translation_key="service_hours",
        value_fn=lambda device: device.service_hours,
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.HOURS,
        suggested_unit_of_measurement=UnitOfTime.DAYS,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    EheimDigitalSensorDescription[EheimDigitalClassicVario](
        key="error_code",
        translation_key="error_code",
        value_fn=lambda device: device.error_code.name.lower(),
        device_class=SensorDeviceClass.ENUM,
        options=[name.lower() for name in FilterErrorCode._member_names_],
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EheimDigitalConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up callbacks for the coordinator to add sensors as devices are found."""
    coordinator = entry.runtime_data

    def async_setup_device_entities(
        device_address: dict[str, EheimDigitalDevice],
    ) -> None:
        """Set up the light entities for one or multiple devices."""
        entities: list[EheimDigitalSensor[Any]] = []
        for device in device_address.values():
            if isinstance(device, EheimDigitalFilter):
                entities += [
                    EheimDigitalSensor[EheimDigitalFilter](
                        coordinator, device, description
                    )
                    for description in FILTER_DESCRIPTIONS
                ]
            if isinstance(device, EheimDigitalClassicVario):
                entities += [
                    EheimDigitalSensor[EheimDigitalClassicVario](
                        coordinator, device, description
                    )
                    for description in CLASSICVARIO_DESCRIPTIONS
                ]

        async_add_entities(entities)

    coordinator.add_platform_callback(async_setup_device_entities)
    async_setup_device_entities(coordinator.hub.devices)


class EheimDigitalSensor[_DeviceT: EheimDigitalDevice](
    EheimDigitalEntity[_DeviceT], SensorEntity
):
    """Represent a EHEIM Digital sensor entity."""

    entity_description: EheimDigitalSensorDescription[_DeviceT]

    def __init__(
        self,
        coordinator: EheimDigitalUpdateCoordinator,
        device: _DeviceT,
        description: EheimDigitalSensorDescription[_DeviceT],
    ) -> None:
        """Initialize an EHEIM Digital number entity."""
        super().__init__(coordinator, device)
        self.entity_description = description
        self._attr_unique_id = f"{self._device_address}_{description.key}"

    @override
    def _async_update_attrs(self) -> None:
        self._attr_native_value = self.entity_description.value_fn(self._device)
