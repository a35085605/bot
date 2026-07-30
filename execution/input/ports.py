from __future__ import annotations

from typing import Protocol, TypeVar

from execution.control import ExecutionOperationResult
from execution.input.domain import (
    KeyChord,
    KeyDown,
    KeyPress,
    KeyUp,
    PointerClick,
    PointerDrag,
    PointerMove,
    PointerScroll,
    TextEntry,
)


PointT = TypeVar("PointT", contravariant=True)


class PointerMover(Protocol[PointT]):
    def move(self, operation: PointerMove[PointT]) -> ExecutionOperationResult:
        ...


class PointerClicker(Protocol[PointT]):
    def click(self, operation: PointerClick[PointT]) -> ExecutionOperationResult:
        ...


class PointerScroller(Protocol[PointT]):
    def scroll(self, operation: PointerScroll[PointT]) -> ExecutionOperationResult:
        ...


class PointerDragger(Protocol[PointT]):
    def drag(self, operation: PointerDrag[PointT]) -> ExecutionOperationResult:
        ...


class KeyStateController(Protocol):
    def key_down(self, operation: KeyDown) -> ExecutionOperationResult:
        ...

    def key_up(self, operation: KeyUp) -> ExecutionOperationResult:
        ...


class KeyPresser(Protocol):
    def press(self, operation: KeyPress) -> ExecutionOperationResult:
        ...


class KeyChordController(Protocol):
    def chord(self, operation: KeyChord) -> ExecutionOperationResult:
        ...


class TextController(Protocol):
    def type_text(self, operation: TextEntry) -> ExecutionOperationResult:
        ...


class BackNavigator(Protocol):
    def back(self) -> ExecutionOperationResult:
        ...
