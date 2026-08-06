from __future__ import annotations

from typing import TYPE_CHECKING, Any

from observation.target_runtime.domain import (
    ControlCapability,
    ControlChannelId,
    ControlChannelKind,
    ControlChannelSnapshot,
    ControlChannelStatus,
    ReadinessBlocker,
    TargetAvailability,
    TargetId,
    TargetRuntimeSnapshot,
)
from observation.target_runtime.ports import (
    ControlChannelInspector,
    TargetRuntimeInspector,
)

if TYPE_CHECKING:
    from adb.observation import (
        AdbChannelInspector,
        AdbChannelState,
        AdbDeviceStatus,
    )
    from desktop_window.observation import (
        FocusStatus,
        WindowChannelInspector,
        WindowChannelState,
    )


def __getattr__(name: str) -> Any:
    """Lazily retain the pre-migration platform observation surface."""

    if name == "AdbChannelInspector":
        from adb.observation import AdbChannelInspector

        return AdbChannelInspector
    if name == "AdbChannelState":
        from adb.observation import AdbChannelState

        return AdbChannelState
    if name == "AdbDeviceStatus":
        from adb.observation import AdbDeviceStatus

        return AdbDeviceStatus
    if name == "FocusStatus":
        from desktop_window.observation import FocusStatus

        return FocusStatus
    if name == "WindowChannelInspector":
        from desktop_window.observation import WindowChannelInspector

        return WindowChannelInspector
    if name == "WindowChannelState":
        from desktop_window.observation import WindowChannelState

        return WindowChannelState
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "AdbChannelInspector",
    "AdbChannelState",
    "AdbDeviceStatus",
    "ControlCapability",
    "ControlChannelId",
    "ControlChannelInspector",
    "ControlChannelKind",
    "ControlChannelSnapshot",
    "ControlChannelStatus",
    "FocusStatus",
    "ReadinessBlocker",
    "TargetAvailability",
    "TargetId",
    "TargetRuntimeInspector",
    "TargetRuntimeSnapshot",
    "WindowChannelInspector",
    "WindowChannelState",
]
