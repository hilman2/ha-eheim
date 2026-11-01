"""Tests for the EHEIM.digital hub."""

import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from custom_components.eheimdigital._vendor.eheimdigital.hub import EheimDigitalHub
from custom_components.eheimdigital._vendor.eheimdigital.types import UsrDtaPacket


@pytest.mark.parametrize("fixture", ["usrdta_heater.json"])
async def test_add_device(fixture: str) -> None:
    """Tests adding a device."""
    usrdta = UsrDtaPacket(
        json.loads(
            (Path(__file__).parent / "fixtures" / fixture).read_text(encoding="utf8")
        )
    )
    hub = EheimDigitalHub(session=Mock())
    await hub.add_device(usrdta)
    assert len(hub.devices) == 1
    assert usrdta["from"] in hub.devices
    assert (device := hub.devices[usrdta["from"]])
    assert device.mac_address == usrdta["from"]
    assert device.device_type == usrdta["version"]
