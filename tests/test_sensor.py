"""Tests for the sensor module."""

from unittest.mock import MagicMock, patch

import pytest
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    get_sensor_display_state,
    snapshot_platform,
)
from syrupy.assertion import SnapshotAssertion

from custom_components.eheimdigital_plus._vendor.eheimdigital.types import (
    FilterErrorCode,
)

from .conftest import init_integration, mock_event

FILTER_ERROR_ENTITY_ID = "sensor.mock_aquarium_mock_filter_error_code"
FILTER_FLOW_ENTITY_ID = "sensor.mock_aquarium_mock_filter_estimated_flow_rate"
FILTER_POWER_ENTITY_ID = "sensor.mock_aquarium_mock_filter_estimated_power"


async def test_setup(
    hass: HomeAssistant,
    eheimdigital_hub_mock: MagicMock,
    mock_config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
) -> None:
    """Test sensor platform setup for the filter."""
    mock_config_entry.add_to_hass(hass)

    with (
        patch("custom_components.eheimdigital_plus.PLATFORMS", [Platform.SENSOR]),
        patch(
            "custom_components.eheimdigital_plus.coordinator.asyncio.Event",
            new=mock_event,
        ),
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)

    for device in eheimdigital_hub_mock.return_value.devices:
        await eheimdigital_hub_mock.call_args.kwargs["device_found_callback"](
            device, eheimdigital_hub_mock.return_value.devices[device].device_type
        )
        await hass.async_block_till_done()

    await snapshot_platform(hass, entity_registry, snapshot, mock_config_entry.entry_id)


@pytest.mark.parametrize(
    ("device_name", "entity_list"),
    [
        (
            "classic_vario_mock",
            [
                (
                    "sensor.mock_aquarium_mock_classicvario_current_speed",
                    "classic_vario_data",
                    "rel_speed",
                    10,
                    10,
                ),
                (
                    "sensor.mock_aquarium_mock_classicvario_error_code",
                    "classic_vario_data",
                    "errorCode",
                    int(FilterErrorCode.ROTOR_STUCK),
                    "rotor_stuck",
                ),
                (
                    "sensor.mock_aquarium_mock_classicvario_remaining_hours_until_service",
                    "classic_vario_data",
                    "serviceHour",
                    100,
                    str(round(100 / 24, 2)),
                ),
            ],
        ),
        (
            "filter_mock",
            [
                (
                    "sensor.mock_aquarium_mock_filter_current_speed",
                    "filter_data",
                    "freq",
                    7200,
                    str(round(72.0, 1)),
                ),
                (
                    "sensor.mock_aquarium_mock_filter_remaining_hours_until_service",
                    "filter_data",
                    "serviceHour",
                    100,
                    str(round(100 / 24, 2)),
                ),
                (
                    "sensor.mock_aquarium_mock_filter_operating_time",
                    "filter_data",
                    "runTime",
                    0,
                    "0.00",
                ),
                (
                    "sensor.mock_aquarium_mock_filter_operating_time",
                    "filter_data",
                    "runTime",
                    61,
                    "1.02",
                ),
                (
                    "sensor.mock_aquarium_mock_filter_remaining_off_time",
                    "filter_data",
                    "turnOffTime",
                    61,
                    1.02,
                ),
                (
                    "sensor.mock_aquarium_mock_filter_remaining_off_time",
                    "filter_data",
                    "turnOffTime",
                    0,
                    "0.00",
                ),
                (
                    "sensor.mock_aquarium_mock_filter_remaining_off_time",
                    "filter_data",
                    "turnOffTime",
                    1,
                    0.02,
                ),
                (
                    "sensor.mock_aquarium_mock_filter_remaining_off_time_after_feeding",
                    "filter_data",
                    "turnTimeFeeding",
                    61,
                    1.02,
                ),
                (
                    "sensor.mock_aquarium_mock_filter_remaining_off_time_after_feeding",
                    "filter_data",
                    "turnTimeFeeding",
                    0,
                    "0.00",
                ),
                (
                    "sensor.mock_aquarium_mock_filter_remaining_off_time_after_feeding",
                    "filter_data",
                    "turnTimeFeeding",
                    1,
                    0.02,
                ),
            ],
        ),
    ],
)
async def test_state_update(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    eheimdigital_hub_mock: MagicMock,
    mock_config_entry: MockConfigEntry,
    device_name: str,
    entity_list: list[tuple[str, str, str, float, float | str]],
    request: pytest.FixtureRequest,
) -> None:
    """Test the sensor state update."""
    device: MagicMock = request.getfixturevalue(device_name)
    await init_integration(hass, mock_config_entry)

    await eheimdigital_hub_mock.call_args.kwargs["device_found_callback"](
        device.mac_address, device.device_type
    )

    await hass.async_block_till_done()

    for item in entity_list:
        getattr(device, item[1])[item[2]] = item[3]
        await eheimdigital_hub_mock.call_args.kwargs["receive_callback"]()
        assert get_sensor_display_state(hass, entity_registry, item[0]) == str(item[4])


@pytest.mark.parametrize(
    ("payload", "entity_id", "expected"),
    [
        pytest.param(
            {"pumpMode": 16}, FILTER_ERROR_ENTITY_ID, "no_error", id="no_error"
        ),
        pytest.param(
            {"pumpMode": 528}, FILTER_ERROR_ENTITY_ID, "rotor_stuck", id="rotor"
        ),
        pytest.param(
            {"pumpMode": 784}, FILTER_ERROR_ENTITY_ID, "air_in_filter", id="air"
        ),
        pytest.param(
            {"pumpMode": 1296},
            FILTER_ERROR_ENTITY_ID,
            "temperature_error",
            id="temperature",
        ),
        pytest.param(
            {"pumpMode": 272},
            FILTER_ERROR_ENTITY_ID,
            "unknown_error",
            id="unknown_error",
        ),
        pytest.param(
            {"pumpMode": 16912},
            FILTER_ERROR_ENTITY_ID,
            "rotor_stuck",
            id="calibration_and_error",
        ),
        pytest.param(
            {"freq": 3500, "dfsFaktor": 683}, FILTER_FLOW_ENTITY_ID, "143", id="flow"
        ),
        pytest.param(
            {"freq": 3500, "dfsFaktor": 683, "filterActive": 0},
            FILTER_FLOW_ENTITY_ID,
            "0",
            id="stopped_flow",
        ),
        pytest.param(
            {"freq": 3500, "dfsFaktor": 683}, FILTER_POWER_ENTITY_ID, "7.80", id="power"
        ),
        pytest.param(
            {"filterActive": 0}, FILTER_POWER_ENTITY_ID, "1.00", id="standby_power"
        ),
        pytest.param(
            {"freq": 8000, "dfsFaktor": 8200},
            FILTER_POWER_ENTITY_ID,
            "unknown",
            id="invalid_power_curve",
        ),
    ],
)
async def test_filter_status_updates(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    eheimdigital_hub_mock: MagicMock,
    mock_config_entry: MockConfigEntry,
    filter_mock: MagicMock,
    payload: dict[str, int],
    entity_id: str,
    expected: str,
) -> None:
    """Expose library status updates as correctly formatted sensor states."""
    await init_integration(hass, mock_config_entry)
    filter_mock.filter_data.update(payload)
    await eheimdigital_hub_mock.call_args.kwargs["receive_callback"]()
    assert get_sensor_display_state(hass, entity_registry, entity_id) == expected
