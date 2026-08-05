"""Desktop-window management contracts.

Window command models remain in ``execution.window.domain`` during the first
migration stage so existing imports and native coordinate types stay compatible.
The management ports defined here are the canonical capability boundary.
"""

from execution.window.domain import (
    WindowActivation,
    WindowBoundsChange,
    WindowMinimize,
    WindowMove,
    WindowResize,
    WindowRestore,
)
from management.window.ports import (
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
