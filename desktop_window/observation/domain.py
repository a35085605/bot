from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from numbers import Integral

from geometry.rect import Rect


def _normalize_optional_text(
    value: object,
    *,
    field_name: str,
) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(
            f"{field_name} must be a string, "
            f"got {type(value).__name__}"
        )
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} cannot be empty")
    return normalized


class FocusStatus(str, Enum):
    UNKNOWN = "unknown"
    TARGET = "target"
    OTHER = "other"
    NONE = "none"


def _validate_optional_bool(
    value: object,
    *,
    field_name: str,
) -> bool | None:
    if value is not None and not isinstance(value, bool):
        raise TypeError(f"{field_name} must be bool or None")
    return value


def _validate_optional_process_id(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise TypeError("window process id must be an integer or None")
    normalized = int(value)
    if normalized <= 0:
        raise ValueError("window process id must be greater than zero")
    return normalized


def _validate_optional_rect(
    value: object,
    *,
    field_name: str,
) -> Rect | None:
    if value is not None and not isinstance(value, Rect):
        raise TypeError(f"{field_name} must be Rect or None")
    return value


@dataclass(frozen=True, slots=True)
class WindowChannelState:
    """Latest observed desktop-window state for one control channel."""

    window_id: str | None = None
    foreground_window_id: str | None = None
    process_id: int | None = None
    title: str | None = None
    client_bounds_screen: Rect | None = None
    window_bounds_screen: Rect | None = None
    focus: FocusStatus = FocusStatus.UNKNOWN
    minimized: bool | None = None
    visible: bool | None = None
    responsive: bool | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.focus, FocusStatus):
            raise TypeError("window focus must be FocusStatus")

        window_id = _normalize_optional_text(
            self.window_id,
            field_name="window id",
        )
        foreground_window_id = _normalize_optional_text(
            self.foreground_window_id,
            field_name="foreground window id",
        )
        process_id = _validate_optional_process_id(self.process_id)
        title = _normalize_optional_text(
            self.title,
            field_name="window title",
        )
        client_bounds_screen = _validate_optional_rect(
            self.client_bounds_screen,
            field_name="window client bounds",
        )
        window_bounds_screen = _validate_optional_rect(
            self.window_bounds_screen,
            field_name="window bounds",
        )
        minimized = _validate_optional_bool(
            self.minimized,
            field_name="window minimized",
        )
        visible = _validate_optional_bool(
            self.visible,
            field_name="window visible",
        )
        responsive = _validate_optional_bool(
            self.responsive,
            field_name="window responsive",
        )

        if (
            window_bounds_screen is not None
            and client_bounds_screen is not None
            and not window_bounds_screen.contains_rect(client_bounds_screen)
        ):
            raise ValueError("window bounds must contain client bounds")

        if self.focus is FocusStatus.TARGET:
            if window_id is None or foreground_window_id is None:
                raise ValueError(
                    "target focus requires target and foreground window ids"
                )
            if window_id != foreground_window_id:
                raise ValueError(
                    "target focus requires the target window to be foreground"
                )
            if minimized is True:
                raise ValueError(
                    "a minimized window cannot hold target focus"
                )
        elif self.focus is FocusStatus.OTHER:
            if foreground_window_id is None:
                raise ValueError(
                    "other focus requires a foreground window id"
                )
            if window_id is not None and window_id == foreground_window_id:
                raise ValueError(
                    "other focus cannot name the target as foreground"
                )
        elif self.focus is FocusStatus.NONE:
            if foreground_window_id is not None:
                raise ValueError(
                    "no focus cannot include a foreground window id"
                )

        object.__setattr__(self, "window_id", window_id)
        object.__setattr__(
            self,
            "foreground_window_id",
            foreground_window_id,
        )
        object.__setattr__(self, "process_id", process_id)
        object.__setattr__(self, "title", title)
        object.__setattr__(
            self,
            "client_bounds_screen",
            client_bounds_screen,
        )
        object.__setattr__(
            self,
            "window_bounds_screen",
            window_bounds_screen,
        )
        object.__setattr__(self, "minimized", minimized)
        object.__setattr__(self, "visible", visible)
        object.__setattr__(self, "responsive", responsive)
