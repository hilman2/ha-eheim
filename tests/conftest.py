"""Configurations for the EHEIM Digital tests."""

import json
from asyncio import Event
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.syrupy import HomeAssistantSnapshotExtension
from syrupy.assertion import SnapshotAssertion

from custom_components.eheimdigital_plus._vendor.eheimdigital.classic_led_ctrl import (
    EheimDigitalClassicLEDControl,
)
from custom_components.eheimdigital_plus._vendor.eheimdigital.classic_vario import (
    EheimDigitalClassicVario,
)
from custom_components.eheimdigital_plus._vendor.eheimdigital.filter import (
    EheimDigitalFilter,
)
from custom_components.eheimdigital_plus._vendor.eheimdigital.heater import (
    EheimDigitalHeater,
)
from custom_components.eheimdigital_plus._vendor.eheimdigital.hub import EheimDigitalHub
from custom_components.eheimdigital_plus._vendor.eheimdigital.reeflex import (
    EheimDigitalReeflexUV,
)
from custom_components.eheimdigital_plus._vendor.eheimdigital.types import (
    AcclimatePacket,
    CCVPacket,
    ClassicVarioDataPacket,
    ClockPacket,
    CloudPacket,
    FilterDataPacket,
    MoonPacket,
    ReeflexDataPacket,
    UsrDtaPacket,
)
from custom_components.eheimdigital_plus.const import DOMAIN


def load_json_object_fixture(filename: str) -> dict[str, Any]:
    """Read a device fixture relative to this test suite."""
    return json.loads((Path(__file__).parent / "fixtures" / filename).read_text())


@pytest.fixture
def snapshot(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    """Normalize Home Assistant's generated IDs and timestamps in snapshots."""
    return snapshot.use_extension(HomeAssistantSnapshotExtension)


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: "eheimdigital"}, unique_id="00:00:00:00:00:01"
    )


@pytest.fixture
def classic_led_ctrl_mock():
    """Mock a classicLEDcontrol device."""
    classic_led_ctrl = EheimDigitalClassicLEDControl(
        MagicMock(spec=EheimDigitalHub),
        UsrDtaPacket(load_json_object_fixture("classic_led_ctrl/usrdta.json")),
    )
    classic_led_ctrl.ccv = CCVPacket(
        load_json_object_fixture("classic_led_ctrl/ccv.json")
    )
    classic_led_ctrl.moon = MoonPacket(
        load_json_object_fixture("classic_led_ctrl/moon.json")
    )
    classic_led_ctrl.acclimate = AcclimatePacket(
        load_json_object_fixture("classic_led_ctrl/acclimate.json")
    )
    classic_led_ctrl.cloud = CloudPacket(
        load_json_object_fixture("classic_led_ctrl/cloud.json")
    )
    classic_led_ctrl.clock = ClockPacket(
        load_json_object_fixture("classic_led_ctrl/clock.json")
    )
    return classic_led_ctrl


@pytest.fixture
def heater_mock():
    """Mock a Heater device."""
    heater = EheimDigitalHeater(
        MagicMock(spec=EheimDigitalHub),
        load_json_object_fixture("heater/usrdta.json"),
    )
    heater.heater_data = load_json_object_fixture("heater/heater_data.json")
    return heater


@pytest.fixture
def classic_vario_mock():
    """Mock a classicVARIO device."""
    classic_vario = EheimDigitalClassicVario(
        MagicMock(spec=EheimDigitalHub),
        UsrDtaPacket(load_json_object_fixture("classic_vario/usrdta.json")),
    )
    classic_vario.classic_vario_data = ClassicVarioDataPacket(
        load_json_object_fixture("classic_vario/classic_vario_data.json")
    )
    return classic_vario


@pytest.fixture
def filter_mock():
    """Mock a filter device."""
    eheim_filter = EheimDigitalFilter(
        MagicMock(spec=EheimDigitalHub),
        UsrDtaPacket(load_json_object_fixture("filter/usrdta.json")),
    )
    eheim_filter.filter_data = FilterDataPacket(
        load_json_object_fixture("filter/filter_data.json")
    )
    return eheim_filter


@pytest.fixture
def reeflex_mock():
    """Mock a reeflex device."""
    eheim_reeflex = EheimDigitalReeflexUV(
        MagicMock(spec=EheimDigitalHub),
        UsrDtaPacket(load_json_object_fixture("reeflex/usrdta.json")),
    )
    eheim_reeflex.reeflex_data = ReeflexDataPacket(
        load_json_object_fixture("reeflex/reeflex_data.json")
    )
    return eheim_reeflex


@pytest.fixture
def eheimdigital_hub_mock(
    classic_led_ctrl_mock: MagicMock,
    heater_mock: MagicMock,
    classic_vario_mock: MagicMock,
    filter_mock: MagicMock,
    reeflex_mock: MagicMock,
) -> Generator[AsyncMock]:
    """Mock eheimdigital hub."""
    with (
        patch(
            "custom_components.eheimdigital_plus.coordinator.EheimDigitalHub",
            spec=EheimDigitalHub,
        ) as eheimdigital_hub_mock,
        patch(
            "custom_components.eheimdigital_plus.config_flow.EheimDigitalHub",
            new=eheimdigital_hub_mock,
        ),
    ):
        eheimdigital_hub_mock.return_value.devices = {
            "00:00:00:00:00:01": classic_led_ctrl_mock,
            "00:00:00:00:00:02": heater_mock,
            "00:00:00:00:00:03": classic_vario_mock,
            "00:00:00:00:00:04": filter_mock,
            "00:00:00:00:00:05": reeflex_mock,
        }
        eheimdigital_hub_mock.return_value.main = classic_led_ctrl_mock
        yield eheimdigital_hub_mock


async def init_integration(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Initialize the integration."""

    mock_config_entry.add_to_hass(hass)
    with patch(
        "custom_components.eheimdigital_plus.coordinator.asyncio.Event", new=mock_event
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)


@pytest.fixture(autouse=True)
def custom_integrations(enable_custom_integrations: None) -> None:
    """Load the installed custom component instead of its Core counterpart."""


def mock_event() -> MagicMock:
    """Allow setup to receive device data without a real WebSocket."""
    event = MagicMock(spec=Event)
    event.wait = AsyncMock()
    return event
