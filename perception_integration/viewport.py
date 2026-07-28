from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from numbers import Real
from typing import Protocol, TypeAlias

import numpy as np

from geometry.point import Point
from geometry.rect import Rect
from observation import (
    CapturedFrame,
    FrameId,
    FrameInfo,
    FramePixels,
    PixelFormat,
)


def _normalize_non_empty_text(value: object, *, field_name: str) -> str:
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


def _normalize_confidence(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError("viewport confidence must be a real number")
    normalized = float(value)
    if not 0.0 <= normalized <= 1.0:
        raise ValueError("viewport confidence must be between 0 and 1")
    return normalized


class ViewportExtractionMethod(str, Enum):
    IDENTITY = "identity"
    CONFIGURED_CROP = "configured_crop"


class ViewportFailureReason(str, Enum):
    FRAME_UNUSABLE = "frame_unusable"
    SOURCE_BOUNDS_OUTSIDE_FRAME = "source_bounds_outside_frame"


@dataclass(frozen=True, slots=True)
class ViewportProvenance:
    extractor_id: str
    method: ViewportExtractionMethod

    def __post_init__(self) -> None:
        if not isinstance(self.method, ViewportExtractionMethod):
            raise TypeError("viewport method must be ViewportExtractionMethod")
        object.__setattr__(
            self,
            "extractor_id",
            _normalize_non_empty_text(
                self.extractor_id,
                field_name="viewport extractor id",
            ),
        )


@dataclass(frozen=True, slots=True)
class ViewportPlacement:
    """Translation from clean viewport-root into raw capture-root."""

    source_bounds_capture: Rect

    def __post_init__(self) -> None:
        if not isinstance(self.source_bounds_capture, Rect):
            raise TypeError("source_bounds_capture must be Rect")

    @property
    def root_bounds(self) -> Rect:
        return Rect(
            x=0,
            y=0,
            width=self.source_bounds_capture.width,
            height=self.source_bounds_capture.height,
        )

    def root_point_to_capture(self, point: Point) -> Point:
        if not isinstance(point, Point):
            raise TypeError("viewport-root point must be Point")
        if not self.root_bounds.contains_point(point.x, point.y):
            raise ValueError("point must be inside viewport root bounds")
        return Point(
            x=self.source_bounds_capture.left + point.x,
            y=self.source_bounds_capture.top + point.y,
        )

    def root_rect_to_capture(self, rect: Rect) -> Rect:
        if not isinstance(rect, Rect):
            raise TypeError("viewport-root rect must be Rect")
        if not self.root_bounds.contains_rect(rect):
            raise ValueError("rect must be inside viewport root bounds")
        return rect.translated(
            dx=self.source_bounds_capture.left,
            dy=self.source_bounds_capture.top,
        )


@dataclass(frozen=True, slots=True)
class PerceptionViewport:
    """
    Clean game image consumed by perception.

    All detector, evidence, and world-model root coordinates begin in this
    viewport-root space rather than in the raw capture-root space.
    """

    source_info: FrameInfo
    pixels: FramePixels = field(
        compare=False,
        hash=False,
        repr=False,
    )
    pixel_format: PixelFormat
    placement: ViewportPlacement
    provenance: ViewportProvenance
    confidence: float = 1.0

    def __post_init__(self) -> None:
        if not isinstance(self.source_info, FrameInfo):
            raise TypeError("viewport source_info must be FrameInfo")
        if not isinstance(self.pixel_format, PixelFormat):
            raise TypeError("viewport pixel_format must be PixelFormat")
        if not isinstance(self.placement, ViewportPlacement):
            raise TypeError("viewport placement must be ViewportPlacement")
        if not isinstance(self.provenance, ViewportProvenance):
            raise TypeError("viewport provenance must be ViewportProvenance")
        if not isinstance(self.pixels, np.ndarray):
            raise TypeError("viewport pixels must be a numpy array")
        if self.pixels.dtype != np.uint8:
            raise TypeError(
                "viewport pixels must be uint8, "
                f"got {self.pixels.dtype}"
            )

        root_bounds = self.placement.root_bounds
        channels = self.pixel_format.channel_count
        if channels == 1:
            expected_shape = (root_bounds.height, root_bounds.width)
        else:
            expected_shape = (
                root_bounds.height,
                root_bounds.width,
                channels,
            )
        if self.pixels.shape != expected_shape:
            raise ValueError(
                "viewport pixel shape must match placement and pixel format: "
                f"expected {expected_shape}, got {self.pixels.shape}"
            )

        frozen = np.frombuffer(
            self.pixels.tobytes(order="C"),
            dtype=np.uint8,
        ).reshape(expected_shape)
        object.__setattr__(self, "pixels", frozen)
        object.__setattr__(
            self,
            "confidence",
            _normalize_confidence(self.confidence),
        )

    @property
    def frame_id(self) -> FrameId:
        return self.source_info.frame_id

    @property
    def source_id(self) -> str:
        return self.source_info.source_id

    @property
    def root_bounds(self) -> Rect:
        return self.placement.root_bounds

    def root_point_to_capture(self, point: Point) -> Point:
        return self.placement.root_point_to_capture(point)

    def root_rect_to_capture(self, rect: Rect) -> Rect:
        return self.placement.root_rect_to_capture(rect)

    def root_point_to_screen(self, point: Point) -> Point:
        return self.source_info.root_point_to_screen(
            self.root_point_to_capture(point)
        )

    def root_rect_to_screen(self, rect: Rect) -> Rect:
        return self.source_info.root_rect_to_screen(
            self.root_rect_to_capture(rect)
        )


@dataclass(frozen=True, slots=True)
class ViewportUnavailable:
    frame_id: FrameId
    reason: ViewportFailureReason
    detail: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.frame_id, FrameId):
            raise TypeError("viewport failure frame_id must be FrameId")
        if not isinstance(self.reason, ViewportFailureReason):
            raise TypeError("viewport failure reason must be ViewportFailureReason")
        object.__setattr__(
            self,
            "detail",
            _normalize_optional_text(
                self.detail,
                field_name="viewport failure detail",
            ),
        )


ViewportExtractionResult: TypeAlias = (
    PerceptionViewport | ViewportUnavailable
)


class ViewportExtractor(Protocol):
    """Observation-to-perception boundary for producing a clean viewport."""

    def __call__(
        self,
        frame: CapturedFrame,
    ) -> ViewportExtractionResult:
        ...


def extract_viewport(
    frame: CapturedFrame,
    *,
    extractor: ViewportExtractor,
) -> ViewportExtractionResult:
    """Run the mandatory raw-capture to clean-viewport boundary."""

    if not isinstance(frame, CapturedFrame):
        raise TypeError("frame must be CapturedFrame")
    result = extractor(frame)
    if not isinstance(result, (PerceptionViewport, ViewportUnavailable)):
        raise TypeError(
            "viewport extractor must return PerceptionViewport or "
            "ViewportUnavailable"
        )
    return result


@dataclass(frozen=True, slots=True)
class IdentityViewportExtractor:
    extractor_id: str = "viewport.identity"

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "extractor_id",
            _normalize_non_empty_text(
                self.extractor_id,
                field_name="viewport extractor id",
            ),
        )

    def __call__(
        self,
        frame: CapturedFrame,
    ) -> ViewportExtractionResult:
        return _crop_viewport(
            frame=frame,
            source_bounds_capture=frame.info.root_bounds,
            provenance=ViewportProvenance(
                extractor_id=self.extractor_id,
                method=ViewportExtractionMethod.IDENTITY,
            ),
        )


@dataclass(frozen=True, slots=True)
class ConfiguredCropViewportExtractor:
    source_bounds_capture: Rect
    extractor_id: str = "viewport.configured_crop"

    def __post_init__(self) -> None:
        if not isinstance(self.source_bounds_capture, Rect):
            raise TypeError("source_bounds_capture must be Rect")
        object.__setattr__(
            self,
            "extractor_id",
            _normalize_non_empty_text(
                self.extractor_id,
                field_name="viewport extractor id",
            ),
        )

    def __call__(
        self,
        frame: CapturedFrame,
    ) -> ViewportExtractionResult:
        return _crop_viewport(
            frame=frame,
            source_bounds_capture=self.source_bounds_capture,
            provenance=ViewportProvenance(
                extractor_id=self.extractor_id,
                method=ViewportExtractionMethod.CONFIGURED_CROP,
            ),
        )


def _crop_viewport(
    *,
    frame: CapturedFrame,
    source_bounds_capture: Rect,
    provenance: ViewportProvenance,
) -> ViewportExtractionResult:
    if not isinstance(frame, CapturedFrame):
        raise TypeError("frame must be CapturedFrame")

    if not frame.quality.usable:
        return ViewportUnavailable(
            frame_id=frame.info.frame_id,
            reason=ViewportFailureReason.FRAME_UNUSABLE,
        )

    capture_bounds = frame.info.root_bounds
    if not capture_bounds.contains_rect(source_bounds_capture):
        return ViewportUnavailable(
            frame_id=frame.info.frame_id,
            reason=ViewportFailureReason.SOURCE_BOUNDS_OUTSIDE_FRAME,
            detail=(
                f"source bounds {source_bounds_capture} are outside "
                f"capture bounds {capture_bounds}"
            ),
        )

    left = source_bounds_capture.left - capture_bounds.left
    top = source_bounds_capture.top - capture_bounds.top
    right = source_bounds_capture.right - capture_bounds.left
    bottom = source_bounds_capture.bottom - capture_bounds.top

    if frame.pixel_format.channel_count == 1:
        pixels = frame.pixels[top:bottom, left:right]
    else:
        pixels = frame.pixels[top:bottom, left:right, :]

    return PerceptionViewport(
        source_info=frame.info,
        pixels=pixels,
        pixel_format=frame.pixel_format,
        placement=ViewportPlacement(
            source_bounds_capture=source_bounds_capture,
        ),
        provenance=provenance,
    )
