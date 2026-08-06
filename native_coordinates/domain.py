from __future__ import annotations

from dataclasses import dataclass
from numbers import Integral


def _normalize_integer(value: object, *, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise TypeError(
            f"{field_name} must be an integer, got {type(value).__name__}"
        )
    return int(value)


@dataclass(frozen=True, slots=True, order=True)
class ScreenPoint:
    """Point in the operating-system virtual-screen coordinate space."""

    x: int
    y: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "x",
            _normalize_integer(self.x, field_name="screen point x"),
        )
        object.__setattr__(
            self,
            "y",
            _normalize_integer(self.y, field_name="screen point y"),
        )


@dataclass(frozen=True, slots=True, order=True)
class DevicePoint:
    """Point in a device-native display coordinate space, such as ADB."""

    x: int
    y: int

    def __post_init__(self) -> None:
        x = _normalize_integer(self.x, field_name="device point x")
        y = _normalize_integer(self.y, field_name="device point y")
        if x < 0 or y < 0:
            raise ValueError("device point coordinates cannot be negative")
        object.__setattr__(self, "x", x)
        object.__setattr__(self, "y", y)
