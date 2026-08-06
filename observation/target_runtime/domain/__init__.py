from __future__ import annotations

from typing import TYPE_CHECKING, Any

from observation.target_runtime.domain.channels import ControlChannelSnapshot
from observation.target_runtime.domain.identities import (
    ControlChannelId,
    ReadinessBlocker,
    TargetId,
)
from observation.target_runtime.domain.readiness import (
    ControlCapability,
    ControlChannelKind,
    ControlChannelStatus,
    TargetAvailability,
)
from observation.target_runtime.domain.snapshots import TargetRuntimeSnapshot

if TYPE_CHECKING:
    from adb.observation.domain import AdbChannelState, AdbDeviceStatus
    from desktop_window.observation.domain import FocusStatus, WindowChannelState


def __getattr__(name: str) -> Any:
    """Lazily retain platform symbols from the former core domain surface."""

    if name == "AdbChannelState":
        from adb.observation.domain import AdbChannelState

        return AdbChannelState
    if name == "AdbDeviceStatus":
        from adb.observation.domain import AdbDeviceStatus

        return AdbDeviceStatus
    if name == "FocusStatus":
        from desktop_window.observation.domain import FocusStatus

        return FocusStatus
    if name == "WindowChannelState":
        from desktop_window.observation.domain import WindowChannelState

        return WindowChannelState
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "AdbChannelState",
    "AdbDeviceStatus",
    "ControlCapability",
    "ControlChannelId",
    "ControlChannelKind",
    "ControlChannelSnapshot",
    "ControlChannelStatus",
    "FocusStatus",
    "ReadinessBlocker",
    "TargetAvailability",
    "TargetId",
    "TargetRuntimeSnapshot",
    "WindowChannelState",
]
