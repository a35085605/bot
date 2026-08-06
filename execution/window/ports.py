"""Compatibility exports for desktop-window management ports.

New code should import these ports from ``desktop_window.management``.
"""

from desktop_window.management.ports import (
    WindowActivator,
    WindowBoundsController,
    WindowMinimizer,
    WindowMover,
    WindowResizer,
    WindowRestorer,
)

__all__ = [
    "WindowActivator",
    "WindowBoundsController",
    "WindowMinimizer",
    "WindowMover",
    "WindowResizer",
    "WindowRestorer",
]
