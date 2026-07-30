from __future__ import annotations

from typing import Protocol

from execution.control import ExecutionOperationResult
from execution.window.domain import (
    WindowActivation,
    WindowBoundsChange,
    WindowMinimize,
    WindowMove,
    WindowResize,
    WindowRestore,
)


class WindowActivator(Protocol):
    def activate(self, operation: WindowActivation) -> ExecutionOperationResult:
        ...


class WindowMinimizer(Protocol):
    def minimize(self, operation: WindowMinimize) -> ExecutionOperationResult:
        ...


class WindowRestorer(Protocol):
    def restore(self, operation: WindowRestore) -> ExecutionOperationResult:
        ...


class WindowMover(Protocol):
    def move(self, operation: WindowMove) -> ExecutionOperationResult:
        ...


class WindowResizer(Protocol):
    def resize(self, operation: WindowResize) -> ExecutionOperationResult:
        ...


class WindowBoundsController(Protocol):
    def set_bounds(
        self,
        operation: WindowBoundsChange,
    ) -> ExecutionOperationResult:
        ...
