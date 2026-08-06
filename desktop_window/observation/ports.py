from __future__ import annotations

from typing import Protocol

from observation.target_runtime.ports import ControlChannelInspector

from desktop_window.observation.domain import WindowChannelState


class WindowChannelInspector(
    ControlChannelInspector[WindowChannelState],
    Protocol,
):
    """Inspect one desktop-window channel without changing window state."""
