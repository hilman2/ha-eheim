# Adapted from Home Assistant Core for ha-eheim. See NOTICE.
"""Data update coordinator for the EHEIM Digital integration."""

import asyncio
from collections.abc import Callable
from datetime import timedelta
from typing import override

from aiohttp import ClientError
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from ._vendor.eheimdigital.device import EheimDigitalDevice
from ._vendor.eheimdigital.hub import EheimDigitalHub
from ._vendor.eheimdigital.types import (
    EheimDeviceType,
    EheimDigitalClientError,
    MsgTitle,
)
from .const import DOMAIN, LOGGER

type AsyncSetupDeviceEntitiesCallback = Callable[[dict[str, EheimDigitalDevice]], None]

type EheimDigitalConfigEntry = ConfigEntry[EheimDigitalUpdateCoordinator]

MAIN_DEVICE_TIMEOUT = 2
UPDATE_INTERVAL = timedelta(seconds=15)
DEVICE_STALE_SECONDS = 120


class EheimDigitalUpdateCoordinator(
    DataUpdateCoordinator[dict[str, EheimDigitalDevice]]
):
    """The EHEIM Digital data update coordinator."""

    config_entry: EheimDigitalConfigEntry

    def __init__(
        self, hass: HomeAssistant, config_entry: EheimDigitalConfigEntry
    ) -> None:
        """Initialize the EHEIM Digital data update coordinator."""
        super().__init__(
            hass,
            LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.main_device_added_event = asyncio.Event()
        self.main_device_complete_event = asyncio.Event()
        self.hub = EheimDigitalHub(
            host=self.config_entry.data[CONF_HOST],
            session=async_get_clientsession(hass),
            loop=hass.loop,
            receive_callback=self._async_receive_callback,
            device_found_callback=self._async_device_found,
            disconnect_callback=self._async_disconnected,
            main_device_added_event=self.main_device_added_event,
        )
        self.known_devices: set[str] = set()
        self.incomplete_devices: set[str] = set()
        self.platform_callbacks: set[AsyncSetupDeviceEntitiesCallback] = set()
        self.device_last_seen: dict[str, float] = {}

    def is_device_available(self, address: str) -> bool:
        """Keep a silent mesh member unavailable until it sends another packet."""
        return address in self.hub.devices and (
            self.hass.loop.time() - self.device_last_seen.get(address, 0)
            <= DEVICE_STALE_SECONDS
        )

    async def _async_disconnected(self) -> None:
        """Mark all entities unavailable as soon as the WebSocket stops."""
        self.async_set_update_error(
            UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="connection_lost",
            )
        )

    def add_platform_callback(
        self,
        async_setup_device_entities: AsyncSetupDeviceEntitiesCallback,
    ) -> None:
        """Add the setup callbacks from a specific platform."""
        self.platform_callbacks.add(async_setup_device_entities)
        self.config_entry.async_on_unload(
            lambda: self.platform_callbacks.discard(async_setup_device_entities)
        )

    async def _async_device_found(
        self, device_address: str, device_type: EheimDeviceType
    ) -> None:
        """Set up a new device found.

        This function is called from the library whenever a new device is added.
        """
        self.device_last_seen[device_address] = self.hass.loop.time()
        if self.hub.devices[device_address].is_missing_data:
            self.incomplete_devices.add(device_address)
            return

        if (
            device_address not in self.known_devices
            or device_address in self.incomplete_devices
        ):
            for platform_callback in self.platform_callbacks:
                platform_callback({device_address: self.hub.devices[device_address]})
            self.known_devices.add(device_address)
            if device_address in self.incomplete_devices:
                self.incomplete_devices.remove(device_address)

    def _async_check_main_device_complete(self) -> None:
        """Flag the main device as ready once the rest of its data arrived."""
        if (main := self.hub.main) is not None and not main.is_missing_data:
            self.main_device_complete_event.set()

    async def _async_receive_callback(
        self, device_address: str | None = None, title: MsgTitle | None = None
    ) -> None:
        now = self.hass.loop.time()
        if device_address is None:
            self.device_last_seen.update(dict.fromkeys(self.hub.devices, now))
        else:
            self.device_last_seen[device_address] = now
        self._async_check_main_device_complete()
        if any(self.incomplete_devices):
            for device_address in self.incomplete_devices.copy():
                if not self.hub.devices[device_address].is_missing_data:
                    await self._async_device_found(
                        device_address, EheimDeviceType.VERSION_UNDEFINED
                    )
        if not self.last_update_success:
            LOGGER.info("Connection to EHEIM Digital recovered")
        self.async_set_updated_data(self.hub.devices)

    @override
    async def _async_setup(self) -> None:
        try:
            await self.hub.connect()
            async with asyncio.timeout(MAIN_DEVICE_TIMEOUT):
                # This event gets triggered when the first message is received from
                # the device, it contains the data necessary to create the main device.
                # This removes the race condition where the main device is accessed
                # before the response from the device is parsed.
                await self.main_device_added_event.wait()
            await self.hub.update()
            async with asyncio.timeout(MAIN_DEVICE_TIMEOUT):
                # A device is announced as soon as it is seen, but the packet
                # carrying the values its device entry is built from can arrive
                # after that, so wait for the rest of the main device as well.
                self._async_check_main_device_complete()
                await self.main_device_complete_event.wait()
            for address in self.hub.devices:
                self.device_last_seen.setdefault(address, self.hass.loop.time())
        except (TimeoutError, ClientError, EheimDigitalClientError) as err:
            await self.hub.close()
            raise ConfigEntryNotReady from err

    @override
    async def _async_update_data(self) -> dict[str, EheimDigitalDevice]:
        try:
            await self.hub.update()
        except (ClientError, EheimDigitalClientError, TimeoutError) as ex:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="communication_error",
                translation_placeholders={"error": str(ex)},
            ) from ex
        return self.data
