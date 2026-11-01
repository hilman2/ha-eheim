# Bundled and adapted for ha-eheim. See LICENSE and ../../NOTICE.
"""The EHEIM reeflexUV+e UV sterilizer."""

from __future__ import annotations

from datetime import time, timedelta, timezone
from functools import cached_property
from logging import getLogger
from typing import Any, ClassVar, cast, override

from .device import EheimDigitalDevice
from .types import (
    EheimDigitalDataMissingError,
    MsgTitle,
    ReeflexDataPacket,
    ReeflexMode,
)

_LOGGER = getLogger(__package__)


class EheimDigitalReeflexUV(EheimDigitalDevice):
    """EHEIM reeflexUV+e UV sterilizer."""

    reeflex_data: ReeflexDataPacket | None = None
    packet_mapping: ClassVar[dict[MsgTitle, set[str]]] = {
        MsgTitle.REEFLEX_DATA: {
            "start_time",
            "daily_burn_time",
            "is_lighting",
            "is_active",
            "sw_on_day",
            "sw_on_night",
            "pause",
            "booster",
            "booster_time",
            "remaining_booster_time",
            "expert",
            "mode",
            "pause_time",
            "remaining_pause_time",
            "is_uvc_connected",
            "time_until_next_service",
        },
        **EheimDigitalDevice.packet_mapping,
    }

    @override
    async def parse_message(self, msg: dict[str, Any]) -> None:
        """Parse a message."""
        if msg["title"] == MsgTitle.REEFLEX_DATA:
            self.reeflex_data = cast(ReeflexDataPacket, msg.copy())

    @override
    async def update(self) -> None:
        """Get the new reeflex state."""
        await self.hub.send_packet(
            {
                "title": MsgTitle.GET_REEFLEX_UVC_DATA,
                "to": self.mac_address,
                "from": "USER",
            }
        )

    async def set_reeflex_uvc_param(self, data: dict[str, Any]) -> None:
        """Send a SET_REEFLEX_UVC_PARAM packet, containing new values from data."""
        if self.reeflex_data is None:
            _LOGGER.error("set_reeflex_uvc_param: No REEFLEX_DATA packet received yet.")
            return
        await self.hub.send_packet(
            {
                "title": MsgTitle.SET_REEFLEX_UVC_PARAM,
                "to": self.mac_address,
                "from": "USER",
                "startTime": self.reeflex_data["startTime"],
                "dailyBurnTime": self.reeflex_data["dailyBurnTime"],
                "isActive": self.reeflex_data["isActive"],
                "swOnDay": self.reeflex_data["swOnDay"],
                "swOnNight": self.reeflex_data["swOnNight"],
                "pause": self.reeflex_data["pause"],
                "booster": self.reeflex_data["booster"],
                "expert": self.reeflex_data["expert"],
                "mode": self.reeflex_data["mode"],
                "pauseTime": self.reeflex_data["pauseTime"],
                "boosterTime": self.reeflex_data["boosterTime"],
                "remainingPauseTime": self.reeflex_data["remainingPauseTime"],
                "remainingBoosterTime": self.reeflex_data["remainingBoosterTime"],
                "isUVCConnected": self.reeflex_data["isUVCConnected"],
                "timeUntilNextService": self.reeflex_data["timeUntilNextService"],
                "sync": self.reeflex_data["sync"],
                "partnerName": self.reeflex_data["partnerName"],
                **data,
            }
        )

    @property
    def start_time(self) -> time:
        """Return the start time for daycycle mode."""
        if self.reeflex_data is None:
            raise EheimDigitalDataMissingError
        return time(
            self.reeflex_data["startTime"] // 60,
            self.reeflex_data["startTime"] % 60,
            tzinfo=timezone(timedelta(minutes=self.usrdta["timezone"])),
        )

    async def set_day_start_time(self, time: time) -> None:
        """Set the day start time for Bio mode."""
        if self.reeflex_data is not None:
            await self.set_reeflex_uvc_param(
                {"startTime": time.hour * 60 + time.minute}
            )

    @property
    def daily_burn_time(self) -> int:
        """Return the daily burn time in minutes."""
        if self.reeflex_data is None:
            raise EheimDigitalDataMissingError
        return self.reeflex_data["dailyBurnTime"]

    async def set_daily_burn_time(self, value: int) -> None:
        """Set the daily burn time of the lamp in minutes."""
        if self.reeflex_data is not None:
            await self.set_reeflex_uvc_param({"dailyBurnTime": value})

    @property
    def is_lighting(self) -> bool:
        """Return whether the lamp is currently turned on."""
        if self.reeflex_data is None:
            raise EheimDigitalDataMissingError
        return bool(self.reeflex_data["isLighting"])

    @property
    def is_active(self) -> bool:
        """Return whether the device is active."""
        if self.reeflex_data is None:
            raise EheimDigitalDataMissingError
        return bool(self.reeflex_data["isActive"])

    async def set_active(self, *, active: bool) -> None:
        """Set whether the device should be active or not."""
        if self.reeflex_data is not None:
            await self.set_reeflex_uvc_param({"isActive": int(active)})

    @property
    def sw_on_day(self) -> bool:
        """Unknown function."""
        if self.reeflex_data is None:
            raise EheimDigitalDataMissingError
        return bool(self.reeflex_data["swOnDay"])

    async def set_sw_on_day(self, *, active: bool) -> None:
        """Unknown function."""
        if self.reeflex_data is not None:
            await self.set_reeflex_uvc_param({"swOnDay": int(active)})

    @property
    def sw_on_night(self) -> bool:
        """Unknown function."""
        if self.reeflex_data is None:
            raise EheimDigitalDataMissingError
        return bool(self.reeflex_data["swOnDay"])

    async def set_sw_on_night(self, *, active: bool) -> None:
        """Unknown function."""
        if self.reeflex_data is not None:
            await self.set_reeflex_uvc_param({"swOnDay": int(active)})

    @property
    def pause(self) -> bool:
        """Return whether the device is paused."""
        if self.reeflex_data is None:
            raise EheimDigitalDataMissingError
        return bool(self.reeflex_data["pause"])

    async def set_pause(self, *, pause: bool) -> None:
        """Set whether the device is paused."""
        if self.reeflex_data is not None:
            await self.set_reeflex_uvc_param({"pause": int(pause)})

    @property
    def booster(self) -> bool:
        """Return whether the booster is active."""
        if self.reeflex_data is None:
            raise EheimDigitalDataMissingError
        return bool(self.reeflex_data["booster"])

    async def set_booster(self, *, active: bool) -> None:
        """Set whether the booster is active."""
        if self.reeflex_data is not None:
            await self.set_reeflex_uvc_param({"booster": int(active)})

    @property
    def booster_time(self) -> int:
        """Return the booster duration in minutes."""
        if self.reeflex_data is None:
            raise EheimDigitalDataMissingError
        return self.reeflex_data["boosterTime"]

    async def set_booster_time(self, value: int) -> None:
        """Set the booster duration in minutes."""
        if self.reeflex_data is not None:
            await self.set_reeflex_uvc_param({"boosterTime": value})

    @property
    def remaining_booster_time(self) -> int:
        """Return the remaining booster time in minutes."""
        if self.reeflex_data is None:
            raise EheimDigitalDataMissingError
        return self.reeflex_data["remainingBoosterTime"]

    @property
    def expert(self) -> bool:
        """Return whether expert mode is active."""
        if self.reeflex_data is None:
            raise EheimDigitalDataMissingError
        return bool(self.reeflex_data["expert"])

    async def set_expert(self, *, active: bool) -> None:
        """Set whether expert mode is active."""
        if self.reeflex_data is not None:
            await self.set_reeflex_uvc_param({"expert": int(active)})

    @property
    def mode(self) -> ReeflexMode:
        """Return the operation mode."""
        if self.reeflex_data is None:
            raise EheimDigitalDataMissingError
        return ReeflexMode(self.reeflex_data["mode"])

    async def set_mode(self, mode: ReeflexMode) -> None:
        """Set the operation mode."""
        if self.reeflex_data is not None:
            await self.set_reeflex_uvc_param({"mode": int(mode)})

    @property
    def pause_time(self) -> int:
        """Return the pause duration in minutes."""
        if self.reeflex_data is None:
            raise EheimDigitalDataMissingError
        return self.reeflex_data["pauseTime"]

    async def set_pause_time(self, value: int) -> None:
        """Set the pause duration in minutes."""
        if self.reeflex_data is not None:
            await self.set_reeflex_uvc_param({"pauseTime": value})

    @property
    def remaining_pause_time(self) -> int:
        """Return the remaining pause time in minutes."""
        if self.reeflex_data is None:
            raise EheimDigitalDataMissingError
        return self.reeflex_data["remainingPauseTime"]

    @property
    def is_uvc_connected(self) -> bool:
        """Return whether a UVC lamp is connected."""
        if self.reeflex_data is None:
            raise EheimDigitalDataMissingError
        return bool(self.reeflex_data["isUVCConnected"])

    @property
    def time_until_next_service(self) -> int:
        """Return the time to the next service in hours."""
        if self.reeflex_data is None:
            raise EheimDigitalDataMissingError
        return self.reeflex_data["timeUntilNextService"]

    @cached_property
    @override
    def model_name(self) -> str | None:
        if self.reeflex_data is None:
            return super().model_name
        match self.reeflex_data["version"]:
            case 5:
                return "reeflexUV+e 500"
            case 8:
                return "reeflexUV+e 800"
            case 15:
                return "reeflexUV+e 1500"
            case 20:
                return "reeflexUV+e 2000"
            case _:
                return super().model_name

    @override
    def as_dict(self) -> dict[str, Any]:
        """Return the device as a dictionary."""
        return {
            "reeflex_data": self.reeflex_data,
            **super().as_dict(),
        }

    @property
    @override
    def is_missing_data(self) -> bool:
        return self.reeflex_data is None
