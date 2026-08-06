from __future__ import annotations

from typing import Protocol

from desktop_window.management.domain import (
    WindowActivation,
    WindowBoundsChange,
    WindowMinimize,
    WindowMove,
    WindowResize,
    WindowRestore,
)
from native_operation import NativeOperationResult


class WindowActivator(Protocol):
    def activate(self, operation: WindowActivation) -> NativeOperationResult:
        ...


class WindowMinimizer(Protocol):
    def minimize(self, operation: WindowMinimize) -> NativeOperationResult:
        ...


class WindowRestorer(Protocol):
    def restore(self, operation: WindowRestore) -> NativeOperationResult:
        ...


class WindowMover(Protocol):
    def move(self, operation: WindowMove) -> NativeOperationResult:
        ...


class WindowResizer(Protocol):
    def resize(self, operation: WindowResize) -> NativeOperationResult:
        ...


class WindowBoundsController(Protocol):
    def set_bounds(
        self,
        operation: WindowBoundsChange,
    ) -> NativeOperationResult:
        ...
