"""Read selected filter status values without changing device settings."""

import argparse
import asyncio
import json
from datetime import UTC, datetime
from typing import Any, override

import aiohttp

from custom_components.eheimdigital_plus._vendor.eheimdigital.filter import (
    EheimDigitalFilter,
)
from custom_components.eheimdigital_plus._vendor.eheimdigital.hub import EheimDigitalHub
from custom_components.eheimdigital_plus._vendor.eheimdigital.types import (
    EheimDigitalClientError,
)

READ_REQUESTS = frozenset({"GET_USRDTA", "GET_FILTER_DATA"})


class ReadOnlyHub(EheimDigitalHub):
    """Reject library requests that could change device settings."""

    @override
    async def send_packet(self, packet: dict[str, Any]) -> None:
        if packet.get("title") not in READ_REQUESTS:
            raise RuntimeError("Blocked a request outside the read-only allowlist")
        await super().send_packet(packet)


async def read_status(host: str) -> dict[str, object]:
    """Read one complete status response, timing out after ten seconds."""
    main_ready = asyncio.Event()
    filter_ready = asyncio.Event()

    async with aiohttp.ClientSession() as session:

        async def receive() -> None:
            if (
                isinstance(hub.main, EheimDigitalFilter)
                and not hub.main.is_missing_data
            ):
                filter_ready.set()

        hub = ReadOnlyHub(
            host=host,
            session=session,
            main_device_added_event=main_ready,
            receive_callback=receive,
        )
        try:
            async with asyncio.timeout(10):
                await hub.connect()
                await main_ready.wait()
                device = hub.main
                if not isinstance(device, EheimDigitalFilter):
                    raise TypeError("The main device is not a professionel 5e filter")
                await hub.update()
                await filter_ready.wait()
                data = device.filter_data
                if data is None:
                    raise RuntimeError("No filter status received")

                return {
                    "observed_at": datetime.now(UTC).isoformat(),
                    "library": "bundled eheimdigital",
                    "model": device.model_name,
                    "software": device.sw_version_pretty,
                    "active": device.is_active,
                    "mode": device.filter_mode.name,
                    "current_speed_hz": device.current_speed,
                    "manual_speed_hz": device.manual_speed,
                    "estimated_flow_lph": device.estimated_flow_rate,
                    "estimated_power_w": device.estimated_power,
                    "error_code": device.error_code.name.lower(),
                    "configured_constant_flow_index": device.const_flow,
                    "service_hours": device.service_hours,
                    "operating_minutes": device.operating_time,
                    "off_seconds": device.turn_off_time,
                    "feeding_pause_seconds": device.turn_feeding_time,
                    "day_start": device.day_start_time.isoformat(),
                    "night_start": device.night_start_time.isoformat(),
                    "error_bits": data["pumpMode"] & 0x0F00,
                    "calibration_bits": data["pumpMode"] & 0xF000,
                }
        finally:
            await hub.close()
            if hub.receive_task is not None:
                await asyncio.gather(hub.receive_task, return_exceptions=True)


def main() -> None:
    """Print the status as JSON or exit with a connection error."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("host", help="Device IP address or hostname, without http://")
    args = parser.parse_args()
    try:
        status = asyncio.run(read_status(args.host))
    except TimeoutError:
        parser.exit(1, "Timed out waiting for filter status\n")
    except (
        aiohttp.ClientError,
        EheimDigitalClientError,
        RuntimeError,
        TypeError,
        ValueError,
    ) as err:
        parser.exit(1, f"Filter query failed: {err}\n")
    print(json.dumps(status, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
