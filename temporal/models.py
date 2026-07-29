from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
import math
from numbers import Real


def _normalize_non_empty_text(value: object, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(
            f"{field_name} must be a string, got {type(value).__name__}"
        )
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} cannot be empty")
    return normalized


@dataclass(frozen=True, slots=True)
class TemporalSnapshot:
    """One observation of wall-clock and monotonic time."""

    observed_at: datetime
    monotonic_seconds: float
    observer_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.observed_at, datetime):
            raise TypeError("observed_at must be datetime")
        if self.observed_at.utcoffset() is None:
            raise ValueError("observed_at must be timezone-aware")
        if isinstance(self.monotonic_seconds, bool) or not isinstance(
            self.monotonic_seconds,
            Real,
        ):
            raise TypeError("monotonic_seconds must be a real number")

        monotonic_seconds = float(self.monotonic_seconds)
        if not math.isfinite(monotonic_seconds):
            raise ValueError("monotonic_seconds must be finite")
        if monotonic_seconds < 0.0:
            raise ValueError("monotonic_seconds cannot be negative")

        object.__setattr__(self, "monotonic_seconds", monotonic_seconds)
        object.__setattr__(
            self,
            "observer_id",
            _normalize_non_empty_text(
                self.observer_id,
                field_name="temporal observer id",
            ),
        )

    @property
    def local_date(self) -> date:
        return self.observed_at.date()

    @property
    def local_time(self) -> time:
        return self.observed_at.timetz()

    @property
    def timezone_name(self) -> str | None:
        return self.observed_at.tzname()
