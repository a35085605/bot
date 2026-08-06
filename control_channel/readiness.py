from __future__ import annotations

from enum import Enum
from typing import ClassVar


def _normalize_non_empty_text(
    value: object,
    *,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise TypeError(
            f"{field_name} must be a string, "
            f"got {type(value).__name__}"
        )
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} cannot be empty")
    return normalized


class ControlChannelKind(str):
    """Extensible stable identifier for one control-channel family."""

    DESKTOP_WINDOW: ClassVar[ControlChannelKind]
    ADB: ClassVar[ControlChannelKind]

    def __new__(cls, value: object) -> ControlChannelKind:
        normalized = _normalize_non_empty_text(
            value,
            field_name="control channel kind",
        )
        return str.__new__(cls, normalized)

    @property
    def value(self) -> str:
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
]
