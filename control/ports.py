from __future__ import annotations

from typing import Protocol, TypeVar

from control.domain import (
    ControlOperationResult,
    KeyChord,
    KeyDown,
    KeyPress,
    KeyUp,
    PointerClick,
    PointerDrag,
    PointerMove,
    PointerScroll,
    TextEntry,
    WindowActivation,
    WindowRestore,
)


PointT = TypeVar("PointT", contravariant=True)


class PointerMover(Protocol[PointT]):
    def move(self, operation: PointerMove[PointT]) -> ControlOperationResult:
        ...


class PointerClicker(Protocol[PointT]):
    def click(self, operation: PointerClick[PointT]) -> ControlOperationResult:
        ...


class PointerScroller(Protocol[PointT]):
    def scroll(self, operation: PointerScroll[PointT]) -> ControlOperationResult:
        ...


class PointerDragger(Protocol[PointT]):
    def drag(self, operation: PointerDrag[PointT]) -> ControlOperationResult:
        ...


class KeyStateController(Protocol):
    def key_down(self, operation: KeyDown) -> ControlOperationResult:
        ...

    def key_up(self, operation: KeyUp) -> ControlOperationResult:
        ...


class KeyPresser(Protocol):
    def press(self, operation: KeyPress) -> ControlOperationResult:
        ...


class KeyChordController(Protocol):
    def chord(self, operation: KeyChord) -> ControlOperationResult:
        ...


class TextController(Protocol):
    def type_text(self, operation: TextEntry) -> ControlOperationResult:
        ...


class BackNavigator(Protocol):
    def back(self) -> ControlOperationResult:
        ...


class WindowActivator(Protocol):
    def activate(
        self,
        operation: WindowActivation,
    ) -> ControlOperationResult:
        ...


class WindowRestorer(Protocol):
    def restore(
        self,
        operation: WindowRestore,
    ) -> ControlOperationResult:
        ...
