from __future__ import annotations

from typing import Protocol

from observation.target_runtime.ports import ControlChannelInspector

from adb.observation.domain import AdbChannelState


class AdbChannelInspector(
    ControlChannelInspector[AdbChannelState],
    Protocol,
):
    """Inspect one ADB channel without changing server or device state."""
