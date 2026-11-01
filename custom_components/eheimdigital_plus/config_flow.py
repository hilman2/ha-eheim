# Adapted from Home Assistant Core for ha-eheim. See NOTICE.
"""Config flow for EHEIM Digital Plus."""

import asyncio
from ipaddress import ip_address
from typing import Any, override

import probatio
from aiohttp import ClientError
from homeassistant.config_entries import (
    SOURCE_RECONFIGURE,
    SOURCE_USER,
    ConfigEntryState,
    ConfigFlow,
    ConfigFlowResult,
)
from homeassistant.const import CONF_HOST
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from ._vendor.eheimdigital.device import EheimDigitalDevice
from ._vendor.eheimdigital.hub import EheimDigitalHub
from ._vendor.eheimdigital.types import EheimDeviceType, EheimDigitalClientError
from .const import CONF_MIGRATE_FROM, DOMAIN, LEGACY_DOMAIN, LOGGER

CONFIG_SCHEMA = probatio.Schema(
    {
        probatio.Required(
            CONF_HOST, default="eheimdigital.local"
        ): selector.TextSelector()
    }
)
SUPPORTED_DEVICE_TYPES = {
    EheimDeviceType.VERSION_EHEIM_EXT_FILTER,
    EheimDeviceType.VERSION_EHEIM_EXT_HEATER,
    EheimDeviceType.VERSION_EHEIM_CLASSIC_VARIO,
    EheimDeviceType.VERSION_EHEIM_CLASSIC_LED_CTRL_PLUS_E,
    EheimDeviceType.VERSION_EHEIM_REEFLEX,
}


class InvalidHostError(ValueError):
    """The address must be a hostname or IP address without a URL path."""


class UnsupportedDeviceError(Exception):
    """The discovered device does not have entity support in this integration."""


class EheimDigitalConfigFlow(ConfigFlow, domain=DOMAIN):
    """Configure a verified EHEIM main device and offer legacy migration."""

    def __init__(self) -> None:
        """Initialize the config flow."""
        super().__init__()
        self.data: dict[str, Any] = {}

    async def _async_identify(self, host: str) -> EheimDigitalDevice:
        """Read the main device identity and close the probe in every outcome."""
        if not host or "://" in host or "/" in host:
            raise InvalidHostError
        if ":" in host:
            try:
                ip_address(host)
            except ValueError as err:
                raise InvalidHostError from err
        ready = asyncio.Event()
        try:
            hub = EheimDigitalHub(
                host=host,
                session=async_get_clientsession(self.hass),
                loop=self.hass.loop,
                main_device_added_event=ready,
            )
        except ValueError as err:
            raise InvalidHostError from err
        try:
            await hub.connect()
            async with asyncio.timeout(2):
                await ready.wait()
            if not isinstance(main := hub.main, EheimDigitalDevice):
                raise EheimDigitalClientError("No device identity received")
            if main.device_type not in SUPPORTED_DEVICE_TYPES:
                raise UnsupportedDeviceError
            return main
        finally:
            await hub.close()

    async def _async_validate(self, host: str) -> tuple[EheimDigitalDevice | None, str]:
        """Map connection and device failures to translated setup errors."""
        try:
            return await self._async_identify(host), ""
        except InvalidHostError:
            return None, "invalid_host"
        except UnsupportedDeviceError:
            return None, "unsupported_device"
        except ClientError, EheimDigitalClientError, TimeoutError:
            return None, "cannot_connect"
        except Exception:
            LOGGER.exception("Unexpected EHEIM setup error")
            return None, "unknown"

    @override
    async def async_step_zeroconf(
        self, discovery_info: ZeroconfServiceInfo
    ) -> ConfigFlowResult:
        """Update an existing address or confirm a newly discovered main device."""
        self.data = {CONF_HOST: discovery_info.host}
        self._async_abort_entries_match(self.data)
        main, error = await self._async_validate(discovery_info.host)
        if main is None:
            return self.async_abort(reason=error)
        await self.async_set_unique_id(main.mac_address)
        self._abort_if_unique_id_configured(updates=self.data)
        return await self.async_step_discovery_confirm()

    async def async_step_discovery_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm a discovered device before creating the entry."""
        if user_input is not None:
            return await self._async_finish_setup()
        self._set_confirm_only()
        return self.async_show_form(step_id="discovery_confirm")

    @override
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Configure a main device by its hostname or IP address."""
        errors: dict[str, str] = {}
        if user_input is not None:
            user_input = {CONF_HOST: user_input[CONF_HOST].strip()}
            self._async_abort_entries_match(user_input)
            main, error = await self._async_validate(user_input[CONF_HOST])
            if main is not None:
                await self.async_set_unique_id(
                    main.mac_address, raise_on_progress=False
                )
                self._abort_if_unique_id_configured()
                self.data = user_input
                return await self._async_finish_setup()
            errors["base"] = error
        return self.async_show_form(
            step_id=SOURCE_USER, data_schema=CONFIG_SCHEMA, errors=errors
        )

    async def _async_finish_setup(self) -> ConfigFlowResult:
        """Offer migration only for a legacy entry with the verified device ID."""
        for entry in self.hass.config_entries.async_entries(LEGACY_DOMAIN):
            if entry.unique_id == self.unique_id:
                self.data[CONF_MIGRATE_FROM] = entry.entry_id
                return await self.async_step_migrate()
        return self.async_create_entry(data=self.data, title=self.data[CONF_HOST])

    async def async_step_migrate(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm moving entities after the legacy entry was disabled."""
        legacy = self.hass.config_entries.async_get_entry(self.data[CONF_MIGRATE_FROM])
        if legacy is not None and (
            legacy.disabled_by is None
            or legacy.state is not ConfigEntryState.NOT_LOADED
        ):
            return self.async_abort(reason="legacy_active")
        if user_input is None:
            self._set_confirm_only()
            return self.async_show_form(step_id="migrate")
        return self.async_create_entry(data=self.data, title=self.data[CONF_HOST])

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Change the address while requiring the same verified device identity."""
        errors: dict[str, str] = {}
        if user_input is not None:
            user_input = {CONF_HOST: user_input[CONF_HOST].strip()}
            self._async_abort_entries_match(user_input)
            main, error = await self._async_validate(user_input[CONF_HOST])
            if main is not None:
                await self.async_set_unique_id(main.mac_address)
                self._abort_if_unique_id_mismatch()
                return self.async_update_reload_and_abort(
                    self._get_reconfigure_entry(), data_updates=user_input
                )
            errors["base"] = error
        return self.async_show_form(
            step_id=SOURCE_RECONFIGURE, data_schema=CONFIG_SCHEMA, errors=errors
        )
