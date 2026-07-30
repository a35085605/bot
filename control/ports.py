"""Compatibility exports for execution capability ports."""

from execution.input import (
    BackNavigator,
    KeyChordController,
    KeyPresser,
    KeyStateController,
    PointerClicker,
    PointerDragger,
    PointerMover,
    PointerScroller,
    TextController,
)
from execution.window import WindowActivator, WindowRestorer

__all__ = [
    "BackNavigator",
    "KeyChordController",
    "KeyPresser",
    "KeyStateController",
    "PointerClicker",
    "PointerDragger",
    "PointerMover",
    "PointerScroller",
    "TextController",
    "WindowActivator",
    "WindowRestorer",
]
