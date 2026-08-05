"""Compatibility exports for window-management capability ports.

New code should import these ports from ``management.window``. The compatibility
module remains during the staged boundary migration and owns no implementation.
"""

from management.window.ports import (
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
