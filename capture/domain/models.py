from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import math
from numbers import Integral, Real
from typing import TypeAlias

from geometry.point import Point
from geometry.rect import Rect
from imaging import ImagePixels, PixelFormat, RasterImage


FramePixels: TypeAlias = ImagePixels


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


@dataclass(frozen=True, slots=True)
class CoordinateTransform:
    """Immutable axis-aligned affine transform between coordinate spaces."""

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
class CaptureSurface:
    """Capture-time surface identity and geometry needed to explain pixels.

    Operational window state such as title, process identity, focus, minimized,
    visibility, and responsiveness belongs to ``target_runtime`` instead.
    """

    surface_id: str
    client_bounds_screen: Rect
    outer_bounds_screen: Rect | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.client_bounds_screen, Rect):
            raise TypeError("client_bounds_screen must be Rect")
        if self.outer_bounds_screen is not None:
            if not isinstance(self.outer_bounds_screen, Rect):
                raise TypeError("outer_bounds_screen must be Rect or None")
            if not self.outer_bounds_screen.contains_rect(
                self.client_bounds_screen
            ):
                raise ValueError(
                    "outer surface bounds must contain client bounds"
                )

        object.__setattr__(
            self,
            "surface_id",
            _normalize_non_empty_text(
                self.surface_id,
                field_name="capture surface id",
            ),
        )


@dataclass(frozen=True, slots=True)
class CaptureQuality:
    """Quality of the captured pixels, not operational target state."""

    usable: bool
    sharpness: float | None = None
    contaminated: bool = False
    detail: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.usable, bool):
            raise TypeError("capture usable must be bool")
        if not isinstance(self.contaminated, bool):
            raise TypeError("capture contaminated must be bool")

        sharpness = self.sharpness
        if sharpness is not None:
            sharpness = _normalize_unit_value(
                sharpness,
                field_name="capture sharpness",
            )
            object.__setattr__(self, "sharpness", sharpness)

        object.__setattr__(
            self,
            "detail",
            _normalize_optional_text(
                self.detail,
                field_name="capture quality detail",
            ),
        )


@dataclass(frozen=True, slots=True)
class FrameInfo:
    """Immutable metadata and coordinate contract for one captured frame."""

    frame_id: FrameId
    stream_id: CaptureStreamId
    captured_at: datetime
    root_bounds: Rect
    source_id: str
    surface: CaptureSurface | None
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
        if self.surface is not None and not isinstance(
            self.surface,
            CaptureSurface,
        ):
            raise TypeError("surface must be CaptureSurface or None")
        if not isinstance(self.root_to_screen, CoordinateTransform):
            raise TypeError("root_to_screen must be CoordinateTransform")
        if (
            self.root_to_screen.source is not CoordinateSpace.ROOT
            or self.root_to_screen.target is not CoordinateSpace.SCREEN
        ):
            raise ValueError("root_to_screen must transform ROOT to SCREEN")

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
    """One immutable raster frame and its capture-time context."""

    info: FrameInfo
    image: RasterImage
    quality: CaptureQuality

    def __post_init__(self) -> None:
        if not isinstance(self.info, FrameInfo):
            raise TypeError("captured frame info must be FrameInfo")
        if not isinstance(self.image, RasterImage):
            raise TypeError("captured frame image must be RasterImage")
        if not isinstance(self.quality, CaptureQuality):
            raise TypeError("captured frame quality must be CaptureQuality")
        if (
            self.image.width != self.info.root_bounds.width
            or self.image.height != self.info.root_bounds.height
        ):
            raise ValueError(
                "captured frame image size must match root bounds: "
                f"expected {self.info.root_bounds.width}x"
                f"{self.info.root_bounds.height}, "
                f"got {self.image.width}x{self.image.height}"
            )

    @property
    def pixels(self) -> FramePixels:
        return self.image.pixels

    @property
    def pixel_format(self) -> PixelFormat:
        return self.image.pixel_format
