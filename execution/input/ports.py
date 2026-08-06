from __future__ import annotations

from typing import Protocol, TypeVar

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
from native_operation import NativeOperationResult


PointT = TypeVar("PointT", contravariant=True)


class PointerMover(Protocol[PointT]):
    def move(self, operation: PointerMove[PointT]) -> NativeOperationResult:
        ...


class PointerClicker(Protocol[PointT]):
    def click(self, operation: PointerClick[PointT]) -> NativeOperationResult:
        ...


class PointerScroller(Protocol[PointT]):
    def scroll(self, operation: PointerScroll[PointT]) -> NativeOperationResult:
        ...


class PointerDragger(Protocol[PointT]):
    def drag(self, operation: PointerDrag[PointT]) -> NativeOperationResult:
        ...


class KeyStateController(Protocol):
    def key_down(self, operation: KeyDown) -> NativeOperationResult:
        ...

    def key_up(self, operation: KeyUp) -> NativeOperationResult:
        ...


class KeyPresser(Protocol):
    def press(self, operation: KeyPress) -> NativeOperationResult:
        ...


class KeyChordController(Protocol):
    def chord(self, operation: KeyChord) -> NativeOperationResult:
        ...


class TextController(Protocol):
    def type_text(self, operation: TextEntry) -> NativeOperationResult:
        ...


class BackNavigator(Protocol):
    def back(self) -> NativeOperationResult:
        ...
