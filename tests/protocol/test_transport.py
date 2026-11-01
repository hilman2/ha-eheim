"""Exercise the bundled WebSocket client with actual device packet decoding."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import ClientError, WSMessage, WSMsgType

from custom_components.eheimdigital_plus._vendor.eheimdigital.filter import (
    EheimDigitalFilter,
)
from custom_components.eheimdigital_plus._vendor.eheimdigital.hub import EheimDigitalHub
from custom_components.eheimdigital_plus._vendor.eheimdigital.types import (
    EheimDigitalClientError,
    MsgTitle,
)


def websocket(messages: list[WSMessage]) -> MagicMock:
    """Return a socket that yields a finite sequence of real aiohttp messages."""
    ws = MagicMock()
    ws.closed = False
    ws.send_json = AsyncMock()
    ws.close = AsyncMock()
    ws.__aiter__.return_value = messages
    return ws


def text_message(data: object) -> WSMessage:
    """Encode a synthetic server frame using the same JSON envelope as the device."""
    return WSMessage(WSMsgType.TEXT, json.dumps(data), "")


@pytest.mark.parametrize("batch", [False, True])
async def test_real_packet_decode_and_commands(
    filter_mock: EheimDigitalFilter, batch: bool
) -> None:
    """Read frames, expose estimates, and encode a command through the real client."""
    packets = [
        dict(filter_mock.usrdta),
        dict(filter_mock.filter_data, freq=3500, dfsFaktor=683),
    ]
    messages = [text_message(packets)] if batch else [text_message(p) for p in packets]
    ws = websocket(messages)
    session = MagicMock(ws_connect=AsyncMock(return_value=ws))
    received = AsyncMock()
    disconnected = AsyncMock()
    main_ready = asyncio.Event()
    hub = EheimDigitalHub(
        session=session,
        receive_callback=received,
        disconnect_callback=disconnected,
        main_device_added_event=main_ready,
    )
    await hub.connect()
    await hub.receive_task
    assert main_ready.is_set()
    assert isinstance(hub.main, EheimDigitalFilter)
    assert hub.main.estimated_flow_rate == 143
    assert hub.main.estimated_power == pytest.approx(7.798875)
    assert received.await_count == 2
    disconnected.assert_awaited_once()
    await hub.update()
    titles = [call.args[0]["title"] for call in ws.send_json.await_args_list]
    assert titles == [MsgTitle.GET_USRDTA, MsgTitle.GET_FILTER_DATA]
    await hub.main.set_sys_led(23)
    assert ws.send_json.call_args.args[0]["sysLED"] == 23
    await hub.close()


async def test_callback_with_device_and_title(filter_mock: EheimDigitalFilter) -> None:
    """The coordinator can identify which mesh device sent a heartbeat."""
    calls = []

    class Receiver:
        async def receive(self, address: str, title: MsgTitle) -> None:
            calls.append((address, title))

    receiver = Receiver()
    hub = EheimDigitalHub(session=MagicMock(), receive_callback=receiver.receive)
    await hub.parse_message(dict(filter_mock.usrdta))
    await hub.parse_message(dict(filter_mock.filter_data))
    assert calls == [
        (filter_mock.mac_address, MsgTitle.USRDTA),
        (filter_mock.mac_address, MsgTitle.FILTER_DATA),
    ]


@pytest.mark.parametrize("closed", [False, True])
async def test_command_without_connection(closed: bool) -> None:
    """A disconnected command must fail instead of pretending the device accepted it."""
    hub = EheimDigitalHub(session=MagicMock())
    if closed:
        hub.ws = websocket([])
        hub.ws.closed = True
    with pytest.raises(EheimDigitalClientError):
        await hub.send_packet({"title": "GET_USRDTA", "to": "ALL", "from": "USER"})


async def test_send_error_is_translated() -> None:
    """Expose aiohttp write errors through the client exception caught by HA actions."""
    hub = EheimDigitalHub(session=MagicMock())
    hub.ws = websocket([])
    hub.ws.send_json.side_effect = ClientError("connection reset")
    with pytest.raises(EheimDigitalClientError):
        await hub.send_packet({"title": "GET_USRDTA"})


@pytest.mark.parametrize(
    "message",
    [
        WSMessage(WSMsgType.ERROR, ClientError("offline"), ""),
        WSMessage(WSMsgType.TEXT, "invalid json", ""),
    ],
)
async def test_receiver_error_notifies_disconnect(message: WSMessage) -> None:
    """Both broken frames and socket errors close the connection and notify HA."""
    disconnected = AsyncMock()
    hub = EheimDigitalHub(session=MagicMock(), disconnect_callback=disconnected)
    hub.ws = websocket([message])
    await hub.receive_messages()
    hub.ws.close.assert_awaited_once()
    disconnected.assert_awaited_once()


async def test_unload_joins_receiver() -> None:
    """A deliberate unload waits for cancellation without reporting an outage."""
    started = asyncio.Event()
    blocked = asyncio.Event()

    async def pending_frames():
        started.set()
        await blocked.wait()
        yield text_message({})

    ws = websocket([])
    ws.__aiter__.side_effect = pending_frames
    session = MagicMock(ws_connect=AsyncMock(return_value=ws))
    disconnected = AsyncMock()
    hub = EheimDigitalHub(session=session, disconnect_callback=disconnected)
    await hub.connect()
    task = hub.receive_task
    await started.wait()
    await hub.close()
    assert task.done()
    assert hub.receive_task is None
    disconnected.assert_not_awaited()


async def test_update_reconnects(filter_mock: EheimDigitalFilter) -> None:
    """Polling reconnects a closed socket and sends read requests again."""
    fresh = websocket([])
    session = MagicMock(ws_connect=AsyncMock(return_value=fresh))
    hub = EheimDigitalHub(session=session)
    await hub.parse_message(dict(filter_mock.usrdta))
    hub.ws = websocket([])
    hub.ws.closed = True
    await hub.update()
    session.ws_connect.assert_awaited_once()
    assert fresh.send_json.await_count == 2
    await hub.close()
