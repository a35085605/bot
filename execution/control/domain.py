from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from numbers import Integral


def _normalize_integer(value: object, *, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise TypeError(
            f"{field_name} must be an integer, got {type(value).__name__}"
        )
    return int(value)


def _normalize_non_empty_text(value: object, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(
            f"{field_name} must be a string, got {type(value).__name__}"
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


def _require_timezone_aware(value: object, *, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be datetime")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value


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


class ExecutionOperationStatus(str, Enum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ExecutionOperationResult:
    """Result of one synchronous native execution operation attempt.

    Success means the adapter completed the requested native operation. It does
    not prove that an application-level effect occurred; orchestration must
    observe and verify that separately.
    """

    status: ExecutionOperationStatus
    backend_id: str
    started_at: datetime
    finished_at: datetime
    native_code: str | None = None
    diagnostic: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.status, ExecutionOperationStatus):
            raise TypeError(
                "execution operation status must be ExecutionOperationStatus"
            )
        started_at = _require_timezone_aware(
            self.started_at,
            field_name="execution operation started_at",
        )
        finished_at = _require_timezone_aware(
            self.finished_at,
            field_name="execution operation finished_at",
        )
        if finished_at < started_at:
            raise ValueError("execution operation cannot finish before it starts")
        object.__setattr__(
            self,
            "backend_id",
            _normalize_non_empty_text(
                self.backend_id,
                field_name="execution backend id",
            ),
        )
        object.__setattr__(
            self,
            "native_code",
            _normalize_optional_text(
                self.native_code,
                field_name="execution native code",
            ),
        )
        object.__setattr__(
            self,
            "diagnostic",
            _normalize_optional_text(
                self.diagnostic,
                field_name="execution diagnostic",
            ),
        )
