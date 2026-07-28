from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import math
from numbers import Integral, Real
from typing import TypeAlias

import numpy as np
import numpy.typing as npt

from geometry.point import Point
from geometry.rect import Rect


FramePixels: TypeAlias = npt.NDArray[np.uint8]


def _normalize_non_empty_text(
    value: object,
    *,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise TypeError(
            f"{field_name} must be a string, "
            f"got {type(value).__name__}"
        )

    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} cannot be empty")

    return normalized


def _normalize_optional_text(
    value: object,
    *,
    field_name: str,
) -> str | None:
    if value is None:
        return None
    return _normalize_non_empty_text(value, field_name=field_name)


def _normalize_finite_real(
    value: object,
    *,
    field_name: str,
) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(
            f"{field_name} must be a real number, "
            f"got {type(value).__name__}"
        )

    normalized = float(value)
    if not math.isfinite(normalized):
        raise ValueError(f"{field_name} must be finite")

    return normalized


def _normalize_unit_value(
    value: object,
    *,
    field_name: str,
) -> float:
    normalized = _normalize_finite_real(
        value,
        field_name=field_name,
    )
    if not 0.0 <= normalized <= 1.0:
        raise ValueError(
            f"{field_name} must be between 0 and 1, "
            f"got {normalized}"
        )
    return normalized


def _normalize_non_negative_integer(
    value: object,
    *,
    field_name: str,
) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise TypeError(
            f"{field_name} must be an integer, "
            f"got {type(value).__name__}"
        )

    normalized = int(value)
    if normalized < 0:
        raise ValueError(f"{field_name} cannot be negative")
    return normalized


@dataclass(frozen=True, slots=True, order=True)
class FrameId:
    """Monotonic frame sequence number within one capture stream."""

    value: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_non_negative_integer(
                self.value,
                field_name="frame id",
            ),
        )


@dataclass(frozen=True, slots=True, order=True)
class CaptureStreamId:
    """Identity of one uninterrupted capture session."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_non_empty_text(
                self.value,
                field_name="capture stream id",
            ),
        )

    def __str__(self) -> str:
        return self.value


class CoordinateSpace(str, Enum):
    ROOT = "root"
    SCREEN = "screen"


class PixelFormat(str, Enum):
    GRAY8 = "gray8"
    BGR24 = "bgr24"
    BGRA32 = "bgra32"

    @property
    def channel_count(self) -> int:
        if self is PixelFormat.GRAY8:
            return 1
        if self is PixelFormat.BGR24:
            return 3
        return 4


@dataclass(frozen=True, slots=True)
class CoordinateTransform:
    """
    Immutable axis-aligned affine transform between coordinate spaces.

    A point is transformed as::

        target_x = source_x * scale_x + offset_x
        target_y = source_y * scale_y + offset_y

    Rectangle conversion uses floor for the leading edges and ceil for the
    trailing edges, so the returned integer rectangle contains the complete
    transformed half-open source rectangle.
    """

    source: CoordinateSpace
    target: CoordinateSpace
    scale_x: float = 1.0
    scale_y: float = 1.0
    offset_x: float = 0.0
    offset_y: float = 0.0

    def __post_init__(self) -> None:
        if not isinstance(self.source, CoordinateSpace):
            raise TypeError("transform source must be CoordinateSpace")
        if not isinstance(self.target, CoordinateSpace):
            raise TypeError("transform target must be CoordinateSpace")
        if self.source is self.target:
            raise ValueError(
                "transform source and target must be different spaces"
            )

        scale_x = _normalize_finite_real(
            self.scale_x,
            field_name="transform scale_x",
        )
        scale_y = _normalize_finite_real(
            self.scale_y,
            field_name="transform scale_y",
        )
        if scale_x <= 0.0 or scale_y <= 0.0:
            raise ValueError("transform scales must be greater than zero")

        object.__setattr__(self, "scale_x", scale_x)
        object.__setattr__(self, "scale_y", scale_y)
        object.__setattr__(
            self,
            "offset_x",
            _normalize_finite_real(
                self.offset_x,
                field_name="transform offset_x",
            ),
        )
        object.__setattr__(
            self,
            "offset_y",
            _normalize_finite_real(
                self.offset_y,
                field_name="transform offset_y",
            ),
        )

    def point(self, point: Point) -> Point:
        if not isinstance(point, Point):
            raise TypeError("point must be Point")
        return Point(
            x=int(round(point.x * self.scale_x + self.offset_x)),
            y=int(round(point.y * self.scale_y + self.offset_y)),
        )

    def rect(self, rect: Rect) -> Rect:
        if not isinstance(rect, Rect):
            raise TypeError("rect must be Rect")

        left = math.floor(rect.left * self.scale_x + self.offset_x)
        top = math.floor(rect.top * self.scale_y + self.offset_y)
        right = math.ceil(rect.right * self.scale_x + self.offset_x)
        bottom = math.ceil(rect.bottom * self.scale_y + self.offset_y)

        return Rect.from_ltrb(
            left=left,
            top=top,
            right=right,
            bottom=bottom,
        )

    def inverse(self) -> CoordinateTransform:
        return CoordinateTransform(
            source=self.target,
            target=self.source,
            scale_x=1.0 / self.scale_x,
            scale_y=1.0 / self.scale_y,
            offset_x=-self.offset_x / self.scale_x,
            offset_y=-self.offset_y / self.scale_y,
        )


@dataclass(frozen=True, slots=True)
class WindowContext:
    """Window state captured atomically with a frame."""

    window_id: str
    client_bounds_screen: Rect
    window_bounds_screen: Rect | None = None
    process_id: int | None = None
    title: str | None = None
    is_foreground: bool = False
    is_minimized: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.client_bounds_screen, Rect):
            raise TypeError("client_bounds_screen must be Rect")
        if self.window_bounds_screen is not None:
            if not isinstance(self.window_bounds_screen, Rect):
                raise TypeError("window_bounds_screen must be Rect or None")
            if not self.window_bounds_screen.contains_rect(
                self.client_bounds_screen
            ):
                raise ValueError(
                    "window bounds must contain client bounds"
                )

        process_id = self.process_id
        if process_id is not None:
            process_id = _normalize_non_negative_integer(
                process_id,
                field_name="window process id",
            )
            if process_id == 0:
                raise ValueError("window process id must be greater than zero")

        if not isinstance(self.is_foreground, bool):
            raise TypeError("is_foreground must be bool")
        if not isinstance(self.is_minimized, bool):
            raise TypeError("is_minimized must be bool")
        if self.is_foreground and self.is_minimized:
            raise ValueError(
                "a minimized window cannot be the foreground window"
            )

        object.__setattr__(
            self,
            "window_id",
            _normalize_non_empty_text(
                self.window_id,
                field_name="window id",
            ),
        )
        object.__setattr__(self, "process_id", process_id)
        object.__setattr__(
            self,
            "title",
            _normalize_optional_text(
                self.title,
                field_name="window title",
            ),
        )


@dataclass(frozen=True, slots=True)
class CaptureQuality:
    usable: bool
    sharpness: float | None = None
    occluded: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.usable, bool):
            raise TypeError("capture usable must be bool")
        if not isinstance(self.occluded, bool):
            raise TypeError("capture occluded must be bool")

        sharpness = self.sharpness
        if sharpness is not None:
            sharpness = _normalize_unit_value(
                sharpness,
                field_name="capture sharpness",
            )
            object.__setattr__(self, "sharpness", sharpness)


@dataclass(frozen=True, slots=True)
class FrameInfo:
    """Immutable metadata and coordinate contract for one captured frame."""

    frame_id: FrameId
    stream_id: CaptureStreamId
    captured_at: datetime
    root_bounds: Rect
    source_id: str
    window: WindowContext | None
    root_to_screen: CoordinateTransform
    capture_backend: str

    def __post_init__(self) -> None:
        if not isinstance(self.frame_id, FrameId):
            raise TypeError("frame_id must be FrameId")
        if not isinstance(self.stream_id, CaptureStreamId):
            raise TypeError("stream_id must be CaptureStreamId")
        if not isinstance(self.captured_at, datetime):
            raise TypeError("captured_at must be datetime")
        if self.captured_at.utcoffset() is None:
            raise ValueError("captured_at must be timezone-aware")
        if not isinstance(self.root_bounds, Rect):
            raise TypeError("root_bounds must be Rect")
        if self.window is not None and not isinstance(
            self.window,
            WindowContext,
        ):
            raise TypeError("window must be WindowContext or None")
        if not isinstance(self.root_to_screen, CoordinateTransform):
            raise TypeError(
                "root_to_screen must be CoordinateTransform"
            )
        if (
            self.root_to_screen.source is not CoordinateSpace.ROOT
            or self.root_to_screen.target is not CoordinateSpace.SCREEN
        ):
            raise ValueError(
                "root_to_screen must transform ROOT to SCREEN"
            )

        object.__setattr__(
            self,
            "source_id",
            _normalize_non_empty_text(
                self.source_id,
                field_name="frame source id",
            ),
        )
        object.__setattr__(
            self,
            "capture_backend",
            _normalize_non_empty_text(
                self.capture_backend,
                field_name="capture backend",
            ),
        )

    @property
    def capture_bounds_screen(self) -> Rect:
        return self.root_to_screen.rect(self.root_bounds)

    def root_point_to_screen(self, point: Point) -> Point:
        if not self.root_bounds.contains_point(point.x, point.y):
            raise ValueError("root point must be inside frame root bounds")
        return self.root_to_screen.point(point)

    def root_rect_to_screen(self, rect: Rect) -> Rect:
        if not self.root_bounds.contains_rect(rect):
            raise ValueError("root rect must be inside frame root bounds")
        return self.root_to_screen.rect(rect)


@dataclass(frozen=True, slots=True)
class CapturedFrame:
    """One independently owned immutable pixel frame and its context."""

    info: FrameInfo
    pixels: FramePixels = field(
        compare=False,
        hash=False,
        repr=False,
    )
    pixel_format: PixelFormat
    quality: CaptureQuality

    def __post_init__(self) -> None:
        if not isinstance(self.info, FrameInfo):
            raise TypeError("captured frame info must be FrameInfo")
        if not isinstance(self.pixel_format, PixelFormat):
            raise TypeError("pixel_format must be PixelFormat")
        if not isinstance(self.quality, CaptureQuality):
            raise TypeError("captured frame quality must be CaptureQuality")
        if not isinstance(self.pixels, np.ndarray):
            raise TypeError("captured frame pixels must be a numpy array")
        if self.pixels.dtype != np.uint8:
            raise TypeError(
                "captured frame pixels must be uint8, "
                f"got {self.pixels.dtype}"
            )

        expected_height = self.info.root_bounds.height
        expected_width = self.info.root_bounds.width
        expected_channels = self.pixel_format.channel_count

        if expected_channels == 1:
            expected_shape = (expected_height, expected_width)
        else:
            expected_shape = (
                expected_height,
                expected_width,
                expected_channels,
            )

        if self.pixels.shape != expected_shape:
            raise ValueError(
                "captured frame pixel shape must match root bounds and "
                f"pixel format: expected {expected_shape}, "
                f"got {self.pixels.shape}"
            )

        frozen = np.frombuffer(
            self.pixels.tobytes(order="C"),
            dtype=np.uint8,
        ).reshape(expected_shape)
        object.__setattr__(self, "pixels", frozen)
