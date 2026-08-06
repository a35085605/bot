"""Desktop-window state and geometry management contracts."""

from desktop_window.management.domain import (
    WindowActivation,
    WindowBoundsChange,
    WindowMinimize,
    WindowMove,
    WindowResize,
    WindowRestore,
)
from desktop_window.management.ports import (
    WindowActivator,
    WindowBoundsController,
    WindowMinimizer,
    WindowMover,
    WindowResizer,
    WindowRestorer,
)

__all__ = [
    "WindowActivation",
    "WindowActivator",
    "WindowBoundsChange",
    "WindowBoundsController",
    "WindowMinimize",
    "WindowMinimizer",
    "WindowMove",
    "WindowMover",
    "WindowResize",
    "WindowResizer",
    "WindowRestore",
    "WindowRestorer",
]
