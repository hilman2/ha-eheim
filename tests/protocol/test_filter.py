# Copyright (c) 2026 Manuel Hilgert <hilman2@gmail.com>
"""Tests for professionel5e status values."""

import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from custom_components.eheimdigital_plus._vendor.eheimdigital.filter import (
    EheimDigitalFilter,
)
from custom_components.eheimdigital_plus._vendor.eheimdigital.types import (
    EheimDigitalDataMissingError,
    FilterDataPacket,
    FilterErrorCodeProf,
    MsgTitle,
    UnitOfMeasurement,
    UsrDtaPacket,
)


@pytest.fixture
def filter_data() -> FilterDataPacket:
    """Return a synthetic filter status packet."""
    path = Path(__file__).parent / "fixtures" / "filter_data.json"
    return FilterDataPacket(**json.loads(path.read_text(encoding="utf8")))


@pytest.fixture
def filter_device(filter_data: FilterDataPacket) -> EheimDigitalFilter:
    """Return a filter backed by synthetic device packets."""
    path = Path(__file__).parent / "fixtures" / "usrdta_filter.json"
    device = EheimDigitalFilter(
        Mock(), UsrDtaPacket(**json.loads(path.read_text(encoding="utf8")))
    )
    device.filter_data = filter_data
    return device


@pytest.mark.parametrize(
    ("pump_mode", "expected"),
    [
        (16, FilterErrorCodeProf.NO_ERROR),
        (16 | 0x0200, FilterErrorCodeProf.ROTOR_STUCK),
        (8 | 0x0300, FilterErrorCodeProf.AIR_IN_FILTER),
        (4 | 0x0500, FilterErrorCodeProf.TEMPERATURE_ERROR),
        (16 | 0x4000, FilterErrorCodeProf.NO_ERROR),
        (1 | 0x4000 | 0x0200, FilterErrorCodeProf.ROTOR_STUCK),
        (16 | 0x0100, FilterErrorCodeProf.UNKNOWN_ERROR),
    ],
)
def test_error_code(
    filter_device: EheimDigitalFilter,
    filter_data: FilterDataPacket,
    pump_mode: int,
    expected: FilterErrorCodeProf,
) -> None:
    """Decode error bits independently of mode and calibration flags."""
    filter_data["pumpMode"] = pump_mode
    assert filter_device.error_code == expected


@pytest.mark.parametrize("unit", list(UnitOfMeasurement))
@pytest.mark.parametrize(
    ("frequency", "factor", "active", "expected"),
    [
        (3500, 683, 1, 143),
        (7200, 1000, 1, 432),
        (0, 683, 1, 0),
        (3500, 0, 1, 400),
        (3500, 4, 1, 400),
        (3625, 0, 1, 420),
        (7200, 0, 1, 860),
        (7500, 0, 1, 860),
        (1750, 0, 1, 200),
        (0, 0, 1, 0),
        (3500, 0, 0, 0),
        (7200, 1000, 0, 0),
    ],
)
def test_estimated_flow_rate(
    *,
    filter_device: EheimDigitalFilter,
    filter_data: FilterDataPacket,
    frequency: int,
    factor: int,
    active: int,
    expected: int,
    unit: UnitOfMeasurement,
) -> None:
    """Return l/h regardless of the device's selected display unit."""
    filter_data["freq"] = frequency
    filter_data["dfsFaktor"] = factor
    filter_data["filterActive"] = active
    filter_device.usrdta["unit"] = unit
    assert filter_device.estimated_flow_rate == expected


@pytest.mark.parametrize(
    ("version", "frequency", "expected"),
    [(76, 7600, 980), (78, 8000, 1065), (78, 3800, 470), (99, 3500, None)],
)
def test_estimated_flow_rate_without_factor(
    filter_device: EheimDigitalFilter,
    filter_data: FilterDataPacket,
    version: int,
    frequency: int,
    expected: int | None,
) -> None:
    """Fall back to each model's own tables and stay unknown without any."""
    filter_data["version"] = version
    filter_data["freq"] = frequency
    filter_data["dfsFaktor"] = 0
    assert filter_device.estimated_flow_rate == expected


@pytest.mark.parametrize(
    ("frequency", "factor", "expected"),
    [
        (3500, 683, 7.798875),
        (5300, 683, 20.183469),
        (5400, 683, 20.125446375),
        (5500, 683, 10.012923595807418),
        (6000, 683, 10.319208324896493),
        (7200, 683, 15.219763990321695),
        (8000, 683, 21.753838210888635),
        (8100, 683, 0.0),
        (3500, 1000, 7.798875),
        (6000, 1000, 13.934933771722108),
        (3500, 8000, 19.2),
        (8000, 8000, 19.2),
        (3500, 10000, 40.0),
        (8000, 10000, 40.0),
    ],
)
def test_estimated_power(
    filter_device: EheimDigitalFilter,
    filter_data: FilterDataPacket,
    frequency: int,
    factor: int,
    expected: float,
) -> None:
    """Match values obtained from the manufacturer's 1.03.2 web interface."""
    filter_data["freq"] = frequency
    filter_data["dfsFaktor"] = factor
    assert filter_device.estimated_power == pytest.approx(expected)


def test_standby_power(
    filter_device: EheimDigitalFilter, filter_data: FilterDataPacket
) -> None:
    """Use the vendor's standby estimate when the pump is stopped."""
    filter_data["filterActive"] = 0
    assert filter_device.estimated_power == 1.0


def test_invalid_power_curve(
    filter_device: EheimDigitalFilter, filter_data: FilterDataPacket
) -> None:
    """An undefined estimate must not stop status updates."""
    filter_data["freq"] = 8000
    filter_data["dfsFaktor"] = 8200
    assert filter_device.estimated_power is None


@pytest.mark.parametrize(
    "property_name", ["error_code", "estimated_flow_rate", "estimated_power"]
)
def test_missing_data(filter_device: EheimDigitalFilter, property_name: str) -> None:
    """Require a status packet before exposing filter values."""
    filter_device.filter_data = None
    with pytest.raises(EheimDigitalDataMissingError):
        getattr(filter_device, property_name)


def test_status_packet_mapping(filter_device: EheimDigitalFilter) -> None:
    """Associate derived values with the packet that refreshes them."""
    assert {"error_code", "estimated_flow_rate", "estimated_power"} <= (
        filter_device.packet_mapping[MsgTitle.FILTER_DATA]
    )


async def test_status_refresh(
    filter_device: EheimDigitalFilter, filter_data: FilterDataPacket
) -> None:
    """Only received packets change the filter's cached status."""
    initial_flow = 143
    updated_flow = 210
    message = dict(filter_data)
    message.update(freq=3500, dfsFaktor=683)
    await filter_device.parse_message(message)
    assert filter_device.estimated_flow_rate == initial_flow
    message["dfsFaktor"] = 1000
    assert filter_device.estimated_flow_rate == initial_flow
    await filter_device.parse_message(message)
    assert filter_device.estimated_flow_rate == updated_flow
