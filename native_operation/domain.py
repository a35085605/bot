from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


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


class NativeOperationStatus(str, Enum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class NativeOperationResult:
    """Result of one synchronous native operation attempt.

    Success means that the adapter completed the requested native operation. It
    does not prove that a control channel reached a desired state or that an
    application-level effect occurred. Callers must observe and verify those
    facts separately.
    """

    status: NativeOperationStatus
    backend_id: str
    started_at: datetime
    finished_at: datetime
    native_code: str | None = None
    diagnostic: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.status, NativeOperationStatus):
            raise TypeError(
                "native operation status must be NativeOperationStatus"
            )
        started_at = _require_timezone_aware(
            self.started_at,
            field_name="native operation started_at",
        )
        finished_at = _require_timezone_aware(
            self.finished_at,
            field_name="native operation finished_at",
        )
        if finished_at < started_at:
            raise ValueError("native operation cannot finish before it starts")
        object.__setattr__(
            self,
            "backend_id",
            _normalize_non_empty_text(
                self.backend_id,
                field_name="native operation backend id",
            ),
        )
        object.__setattr__(
            self,
            "native_code",
            _normalize_optional_text(
                self.native_code,
                field_name="native operation code",
            ),
        )
        object.__setattr__(
            self,
            "diagnostic",
            _normalize_optional_text(
                self.diagnostic,
                field_name="native operation diagnostic",
            ),
        )
