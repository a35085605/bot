from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from capture import CapturedFrame
from target_runtime import TargetRuntimeSnapshot
from temporal import TemporalSnapshot


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
class ObservationCoherence:
    """Timing relationship between independently acquired observations."""

    maximum_skew: timedelta
    capture_skew: timedelta | None = None
    runtime_skew: timedelta | None = None

    def __post_init__(self) -> None:
        for field_name, value in (
            ("maximum_skew", self.maximum_skew),
            ("capture_skew", self.capture_skew),
            ("runtime_skew", self.runtime_skew),
        ):
            if value is not None and not isinstance(value, timedelta):
                raise TypeError(f"{field_name} must be timedelta or None")
            if value is not None and value < timedelta(0):
                raise ValueError(f"{field_name} cannot be negative")


@dataclass(frozen=True, slots=True)
class ObservationBundle:
    """Snapshots collected during one orchestration cycle.

    The members are not assumed to be atomic. Each snapshot retains its own
    timestamp and ``coherence`` makes acquisition skew explicit.
    """

    cycle_id: str
    temporal: TemporalSnapshot
    capture: CapturedFrame | None = None
    runtime: TargetRuntimeSnapshot | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.temporal, TemporalSnapshot):
            raise TypeError("temporal must be TemporalSnapshot")
        if self.capture is not None and not isinstance(
            self.capture,
            CapturedFrame,
        ):
            raise TypeError("capture must be CapturedFrame or None")
        if self.runtime is not None and not isinstance(
            self.runtime,
            TargetRuntimeSnapshot,
        ):
            raise TypeError("runtime must be TargetRuntimeSnapshot or None")
        object.__setattr__(
            self,
            "cycle_id",
            _normalize_non_empty_text(
                self.cycle_id,
                field_name="observation cycle id",
            ),
        )

    @property
    def coherence(self) -> ObservationCoherence:
        reference = self.temporal.observed_at
        capture_skew = (
            None
            if self.capture is None
            else abs(reference - self.capture.info.captured_at)
        )
        runtime_skew = (
            None
            if self.runtime is None
            else abs(reference - self.runtime.observed_at)
        )
        skews = tuple(
            skew
            for skew in (capture_skew, runtime_skew)
            if skew is not None
        )
        maximum_skew = max(skews, default=timedelta(0))
        return ObservationCoherence(
            maximum_skew=maximum_skew,
            capture_skew=capture_skew,
            runtime_skew=runtime_skew,
        )
