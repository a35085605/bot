"""Public contracts for independently acquired observation families.

Capture, Target Runtime, and Temporal live under the ``observation`` namespace
and remain separate read-only boundaries. ``ObservationBundle`` coordinates the
snapshots requested for one orchestration cycle while preserving each family's
own timestamp and domain model.
"""

from __future__ import annotations

from typing import Any

from observation.capture import *
from observation.capture import __all__ as _capture_all
from observation.domain.models import (
    ObservationBundle,
    ObservationCoherence,
)
from observation.target_runtime import (
    ControlCapability,
    ControlChannelId,
    ControlChannelInspector,
    ControlChannelKind,
    ControlChannelSnapshot,
    ControlChannelStatus,
    ReadinessBlocker,
    TargetAvailability,
    TargetId,
    TargetRuntimeInspector,
    TargetRuntimeSnapshot,
)
from observation.target_runtime import __all__ as _target_runtime_all
from observation.temporal import *
from observation.temporal import __all__ as _temporal_all


_PLATFORM_TARGET_RUNTIME_EXPORTS = frozenset(
    {
        "AdbChannelInspector",
        "AdbChannelState",
        "AdbDeviceStatus",
        "FocusStatus",
        "WindowChannelInspector",
        "WindowChannelState",
    }
)


def __getattr__(name: str) -> Any:
    """Lazily retain platform exports from the observation facade."""

    if name in _PLATFORM_TARGET_RUNTIME_EXPORTS:
        import observation.target_runtime as target_runtime

        return getattr(target_runtime, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    *_capture_all,
    *_target_runtime_all,
    *_temporal_all,
    "ObservationBundle",
    "ObservationCoherence",
]
