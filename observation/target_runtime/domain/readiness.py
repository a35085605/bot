from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any, ClassVar

from observation.target_runtime.domain.identities import (
    normalize_non_empty_text,
)

if TYPE_CHECKING:
    from adb.observation.domain import AdbDeviceStatus
    from desktop_window.observation.domain import FocusStatus


class TargetAvailability(str, Enum):
    UNKNOWN = "unknown"
    MISSING = "missing"
    AVAILABLE = "available"


class ControlChannelKind(str):
    """Extensible stable identifier for one control-channel family.

    Built-in Window and ADB constants remain available for compatibility.
    External packages may construct additional normalized values without
    modifying the interaction kernel.
    """

    DESKTOP_WINDOW: ClassVar[ControlChannelKind]
    ADB: ClassVar[ControlChannelKind]

    def __new__(cls, value: object) -> ControlChannelKind:
        normalized = normalize_non_empty_text(
            value,
            field_name="control channel kind",
        )
        return str.__new__(cls, normalized)

    @property
    def value(self) -> str:
        """Return the normalized value for previous Enum-style callers."""

        return str(self)


ControlChannelKind.DESKTOP_WINDOW = ControlChannelKind("desktop_window")
ControlChannelKind.ADB = ControlChannelKind("adb")


class ControlChannelStatus(str, Enum):
    UNKNOWN = "unknown"
    UNAVAILABLE = "unavailable"
    BLOCKED = "blocked"
    READY = "ready"


class ControlCapability(str, Enum):
    POINTER = "pointer"
    KEYBOARD = "keyboard"
    TEXT = "text"
    BACK = "back"


def __getattr__(name: str) -> Any:
    """Lazily retain pre-migration platform status imports."""

    if name == "AdbDeviceStatus":
        from adb.observation.domain import AdbDeviceStatus

        return AdbDeviceStatus
    if name == "FocusStatus":
        from desktop_window.observation.domain import FocusStatus

        return FocusStatus
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "AdbDeviceStatus",
    "ControlCapability",
    "ControlChannelKind",
    "ControlChannelStatus",
    "FocusStatus",
    "TargetAvailability",
]
