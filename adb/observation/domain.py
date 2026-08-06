from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


def _normalize_optional_text(
    value: object,
    *,
    field_name: str,
) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(
            f"{field_name} must be a string, "
            f"got {type(value).__name__}"
        )
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} cannot be empty")
    return normalized


class AdbDeviceStatus(str, Enum):
    UNKNOWN = "unknown"
    MISSING = "missing"
    UNAUTHORIZED = "unauthorized"
    OFFLINE = "offline"
    ONLINE = "online"


def _validate_optional_bool(
    value: object,
    *,
    field_name: str,
) -> bool | None:
    if value is not None and not isinstance(value, bool):
        raise TypeError(f"{field_name} must be bool or None")
    return value


@dataclass(frozen=True, slots=True)
class AdbChannelState:
    """Observed ADB server, device, and transport state."""

    serial: str | None = None
    server_reachable: bool | None = None
    device_status: AdbDeviceStatus = AdbDeviceStatus.UNKNOWN
    transport_ready: bool | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.device_status, AdbDeviceStatus):
            raise TypeError("ADB device status must be AdbDeviceStatus")

        serial = _normalize_optional_text(
            self.serial,
            field_name="ADB device serial",
        )
        server_reachable = _validate_optional_bool(
            self.server_reachable,
            field_name="ADB server reachable",
        )
        transport_ready = _validate_optional_bool(
            self.transport_ready,
            field_name="ADB transport ready",
        )

        if self.device_status is AdbDeviceStatus.ONLINE and serial is None:
            raise ValueError("an online ADB device requires a serial")
        if transport_ready is True:
            if server_reachable is not True:
                raise ValueError(
                    "a ready ADB transport requires a reachable server"
                )
            if self.device_status is not AdbDeviceStatus.ONLINE:
                raise ValueError(
                    "a ready ADB transport requires an online device"
                )

        object.__setattr__(self, "serial", serial)
        object.__setattr__(
            self,
            "server_reachable",
            server_reachable,
        )
        object.__setattr__(self, "transport_ready", transport_ready)
