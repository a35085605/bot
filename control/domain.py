"""Compatibility exports for execution capability domain models.

New code should import these contracts from ``execution`` or its capability
subpackages. The implementation now lives under ``execution/``.
"""

from execution.control import (
    DevicePoint,
    ExecutionOperationResult,
    ExecutionOperationStatus,
    ScreenPoint,
)
from execution.input import (
    Key,
    KeyChord,
    KeyDown,
    KeyPress,
    KeyUp,
    PointerButton,
    PointerClick,
    PointerDrag,
    PointerMove,
    PointerScroll,
    ScrollDelta,
    TextEntry,
)
from execution.window import WindowActivation, WindowRestore

ControlOperationResult = ExecutionOperationResult
ControlOperationStatus = ExecutionOperationStatus

__all__ = [
    "ControlOperationResult",
    "ControlOperationStatus",
    "DevicePoint",
    "Key",
    "KeyChord",
    "KeyDown",
    "KeyPress",
    "KeyUp",
    "PointerButton",
    "PointerClick",
    "PointerDrag",
    "PointerMove",
    "PointerScroll",
    "ScreenPoint",
    "ScrollDelta",
    "TextEntry",
    "WindowActivation",
    "WindowRestore",
]
