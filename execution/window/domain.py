from __future__ import annotations

from dataclasses import dataclass

from execution.control import ScreenPoint
from geometry.rect import Rect
from geometry.size import Size


def _normalize_non_empty_text(value: object, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(
            f"{field_name} must be a string, got {type(value).__name__}"
        )
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} cannot be empty")
    return normalized


@dataclass(frozen=True, slots=True)
class WindowActivation:
    """Request platform activation; this is not a focus guarantee."""

    window_id: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "window_id",
            _normalize_non_empty_text(
                self.window_id,
                field_name="window activation id",
            ),
        )


@dataclass(frozen=True, slots=True)
class WindowMinimize:
    window_id: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "window_id",
            _normalize_non_empty_text(
                self.window_id,
                field_name="window minimize id",
            ),
        )


@dataclass(frozen=True, slots=True)
class WindowRestore:
    """Request the platform to restore a minimized window."""

    window_id: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "window_id",
            _normalize_non_empty_text(
                self.window_id,
                field_name="window restore id",
            ),
        )


@dataclass(frozen=True, slots=True)
class WindowMove:
    window_id: str
    top_left_screen: ScreenPoint

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "window_id",
            _normalize_non_empty_text(
                self.window_id,
                field_name="window move id",
            ),
        )
        if not isinstance(self.top_left_screen, ScreenPoint):
            raise TypeError("top_left_screen must be ScreenPoint")


@dataclass(frozen=True, slots=True)
class WindowResize:
    window_id: str
    size: Size

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "window_id",
            _normalize_non_empty_text(
                self.window_id,
                field_name="window resize id",
            ),
        )
        if not isinstance(self.size, Size):
            raise TypeError("window resize size must be Size")


@dataclass(frozen=True, slots=True)
class WindowBoundsChange:
    """Atomically request a new outer window rectangle when supported."""

    window_id: str
    bounds_screen: Rect

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "window_id",
            _normalize_non_empty_text(
                self.window_id,
                field_name="window bounds id",
            ),
        )
        if not isinstance(self.bounds_screen, Rect):
            raise TypeError("bounds_screen must be Rect")
