"""Ensure debug logs do not expose credentials sent by the device."""

import logging
from unittest.mock import MagicMock

import pytest

from custom_components.eheimdigital_plus._vendor.eheimdigital.filter import (
    EheimDigitalFilter,
)
from custom_components.eheimdigital_plus._vendor.eheimdigital.hub import EheimDigitalHub


async def test_packet_credentials_are_not_logged(
    filter_mock: EheimDigitalFilter, caplog: pytest.LogCaptureFixture
) -> None:
    """Keep raw payloads out of logs, including user data and unknown packets."""
    hub = EheimDigitalHub(session=MagicMock())
    packet = dict(filter_mock.usrdta, api_password="packet-secret-marker")
    with caplog.at_level(logging.DEBUG):
        await hub.parse_message(packet)
        await hub.parse_message(
            {"from": packet["from"], "title": "NETCONFIG", "psk": "wifi-secret-marker"}
        )
    assert "Received user data" in caplog.text
    assert "packet-secret-marker" not in caplog.text
    assert "wifi-secret-marker" not in caplog.text
