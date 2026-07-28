from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from numbers import Integral
from typing import Generic, TypeVar


PointT = TypeVar("PointT")


def _normalize_integer(value: object, *, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise TypeError(
            f"{field_name} must be an integer, "
            f"got {type(value).__name__}"
        )
    return int(value)


def _normalize_positive_integer(value: object, *, field_name: str) -> int:
    normalized = _normalize_integer(value, field_name=field_name)
    if normalized <= 0:
        raise ValueError(f"{field_name} must be greater than zero")
    return normalized


def _normalize_non_empty_text(value: object, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(
            f"{field_name} must be a string, "
            f"got {type(value).__name__}"
        )
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} cannot be empty")
    return normalized


def _normalize_optional_text(
    value: object,
    *,
    field_name: str,
) -> str | None:
    if value is None:
        return None
    return _normalize_non_empty_text(value, field_name=field_name)


def _normalize_non_negative_duration(
    value: object,
    *,
    field_name: str,
) -> timedelta:
    if not isinstance(value, timedelta):
        raise TypeError(f"{field_name} must be timedelta")
    if value < timedelta(0):
        raise ValueError(f"{field_name} cannot be negative")
    return value


def _require_timezone_aware(value: object, *, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be datetime")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value


@dataclass(frozen=True, slots=True, order=True)
class ScreenPoint:
    """Point in the operating system virtual-screen coordinate space."""

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


@dataclass(frozen=True, slots=True)
class ScrollDelta:
    """Semantic scroll steps, independent of backend-native units."""

    horizontal_steps: int = 0
    vertical_steps: int = 0

    def __post_init__(self) -> None:
        horizontal = _normalize_integer(
            self.horizontal_steps,
            field_name="horizontal scroll steps",
        )
        vertical = _normalize_integer(
            self.vertical_steps,
            field_name="vertical scroll steps",
        )
        if horizontal == 0 and vertical == 0:
            raise ValueError("scroll delta must contain at least one step")
        object.__setattr__(self, "horizontal_steps", horizontal)
        object.__setattr__(self, "vertical_steps", vertical)


class PointerButton(str, Enum):
    LEFT = "left"
    RIGHT = "right"
    MIDDLE = "middle"


@dataclass(frozen=True, slots=True)
class PointerMove(Generic[PointT]):
    point: PointT
    duration: timedelta = timedelta(0)

    def __post_init__(self) -> None:
        if self.point is None:
            raise TypeError("pointer move point cannot be None")
        object.__setattr__(
            self,
            "duration",
            _normalize_non_negative_duration(
                self.duration,
                field_name="pointer move duration",
            ),
        )


@dataclass(frozen=True, slots=True)
class PointerClick(Generic[PointT]):
    point: PointT
    button: PointerButton = PointerButton.LEFT
    count: int = 1
    interval: timedelta = timedelta(0)

    def __post_init__(self) -> None:
        if self.point is None:
            raise TypeError("pointer click point cannot be None")
        if not isinstance(self.button, PointerButton):
            raise TypeError("pointer click button must be PointerButton")
        object.__setattr__(
            self,
            "count",
            _normalize_positive_integer(
                self.count,
                field_name="pointer click count",
            ),
        )
        object.__setattr__(
            self,
            "interval",
            _normalize_non_negative_duration(
                self.interval,
                field_name="pointer click interval",
            ),
        )


@dataclass(frozen=True, slots=True)
class PointerScroll(Generic[PointT]):
    delta: ScrollDelta
    origin: PointT | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.delta, ScrollDelta):
            raise TypeError("pointer scroll delta must be ScrollDelta")


@dataclass(frozen=True, slots=True)
class PointerDrag(Generic[PointT]):
    start: PointT
    end: PointT
    button: PointerButton = PointerButton.LEFT
    duration: timedelta = timedelta(0)

    def __post_init__(self) -> None:
        if self.start is None or self.end is None:
            raise TypeError("pointer drag points cannot be None")
        if not isinstance(self.button, PointerButton):
            raise TypeError("pointer drag button must be PointerButton")
        object.__setattr__(
            self,
            "duration",
            _normalize_non_negative_duration(
                self.duration,
                field_name="pointer drag duration",
            ),
        )


@dataclass(frozen=True, slots=True, order=True)
class Key:
    """Backend-independent identity for a physical or logical key."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_non_empty_text(self.value, field_name="key"),
        )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class KeyDown:
    key: Key

    def __post_init__(self) -> None:
        if not isinstance(self.key, Key):
            raise TypeError("key_down key must be Key")


@dataclass(frozen=True, slots=True)
class KeyUp:
    key: Key

    def __post_init__(self) -> None:
        if not isinstance(self.key, Key):
            raise TypeError("key_up key must be Key")


@dataclass(frozen=True, slots=True)
class KeyPress:
    key: Key
    repeat: int = 1
    interval: timedelta = timedelta(0)

    def __post_init__(self) -> None:
        if not isinstance(self.key, Key):
            raise TypeError("key press key must be Key")
        object.__setattr__(
            self,
            "repeat",
            _normalize_positive_integer(
                self.repeat,
                field_name="key press repeat",
            ),
        )
        object.__setattr__(
            self,
            "interval",
            _normalize_non_negative_duration(
                self.interval,
                field_name="key press interval",
            ),
        )


@dataclass(frozen=True, slots=True)
class KeyChord:
    keys: tuple[Key, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.keys, tuple):
            raise TypeError("key chord keys must be a tuple")
        if len(self.keys) < 2:
            raise ValueError("key chord requires at least two keys")
        for index, key in enumerate(self.keys):
            if not isinstance(key, Key):
                raise TypeError(f"key chord keys[{index}] must be Key")
        if len(set(self.keys)) != len(self.keys):
            raise ValueError("key chord cannot contain duplicate keys")


@dataclass(frozen=True, slots=True)
class TextEntry:
    text: str

    def __post_init__(self) -> None:
        if not isinstance(self.text, str):
            raise TypeError("text entry must be a string")
        if not self.text:
            raise ValueError("text entry cannot be empty")


@dataclass(frozen=True, slots=True)
class WindowActivation:
    """Request platform activation; this is not a focus guarantee."""

    window_id: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "window_id",
            _normalize_non_empty_text(
                self.window_id,
                field_name="window activation id",
            ),
        )


@dataclass(frozen=True, slots=True)
class WindowRestore:
    """Request the platform to restore a minimized window."""

    window_id: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "window_id",
            _normalize_non_empty_text(
                self.window_id,
                field_name="window restore id",
            ),
        )


class ControlOperationStatus(str, Enum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ControlOperationResult:
    """Result of one synchronous native control operation attempt."""

    status: ControlOperationStatus
    backend_id: str
    started_at: datetime
    finished_at: datetime
    native_code: str | None = None
    diagnostic: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.status, ControlOperationStatus):
            raise TypeError(
                "control operation status must be ControlOperationStatus"
            )
        started_at = _require_timezone_aware(
            self.started_at,
            field_name="control operation started_at",
        )
        finished_at = _require_timezone_aware(
            self.finished_at,
            field_name="control operation finished_at",
        )
        if finished_at < started_at:
            raise ValueError("control operation cannot finish before it starts")
        object.__setattr__(
            self,
            "backend_id",
            _normalize_non_empty_text(
                self.backend_id,
                field_name="control backend id",
            ),
        )
        object.__setattr__(
            self,
            "native_code",
            _normalize_optional_text(
                self.native_code,
                field_name="control native code",
            ),
        )
        object.__setattr__(
            self,
            "diagnostic",
            _normalize_optional_text(
                self.diagnostic,
                field_name="control diagnostic",
            ),
        )
