from __future__ import annotations

from enum import Enum
from typing import ClassVar

from observation.target_runtime.domain.identities import (
    normalize_non_empty_text,
)


class TargetAvailability(str, Enum):
    UNKNOWN = "unknown"
    MISSING = "missing"
    AVAILABLE = "available"


class ControlChannelKind(str):
    """Extensible stable identifier for one control-channel family.

    Built-in Window and ADB constants identify the built-in channel families.
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


__all__ = [
    "ControlCapability",
    "ControlChannelKind",
    "ControlChannelStatus",
    "TargetAvailability",
]
