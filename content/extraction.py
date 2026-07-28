from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from numbers import Real
from typing import Protocol, TypeAlias

import numpy as np

from content.models import ContentFrame, ContentPlacementInCapture
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
            f"{field_name} must be a string, got {type(value).__name__}"
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
        raise TypeError("content extraction confidence must be a real number")
    normalized = float(value)
    if not 0.0 <= normalized <= 1.0:
        raise ValueError(
            "content extraction confidence must be between 0 and 1"
        )
    return normalized


class ContentExtractionMethod(str, Enum):
    IDENTITY = "identity"
    CONFIGURED_CROP = "configured_crop"


class ContentFailureReason(str, Enum):
    FRAME_UNUSABLE = "frame_unusable"
    BOUNDS_OUTSIDE_CAPTURE = "bounds_outside_capture"


@dataclass(frozen=True, slots=True)
class ContentExtractionProvenance:
    extractor_id: str
    method: ContentExtractionMethod

    def __post_init__(self) -> None:
        if not isinstance(self.method, ContentExtractionMethod):
            raise TypeError("method must be ContentExtractionMethod")
        object.__setattr__(
            self,
            "extractor_id",
            _normalize_non_empty_text(
                self.extractor_id,
                field_name="content extractor id",
            ),
        )


@dataclass(frozen=True, slots=True)
class CapturedContent:
    """Clean pixels and content-space context derived from one raw capture."""

    frame: ContentFrame
    pixels: FramePixels = field(compare=False, hash=False, repr=False)
    pixel_format: PixelFormat
    provenance: ContentExtractionProvenance
    confidence: float = 1.0

    def __post_init__(self) -> None:
        if not isinstance(self.frame, ContentFrame):
            raise TypeError("frame must be ContentFrame")
        if not isinstance(self.pixel_format, PixelFormat):
            raise TypeError("pixel_format must be PixelFormat")
        if not isinstance(self.provenance, ContentExtractionProvenance):
            raise TypeError(
                "provenance must be ContentExtractionProvenance"
            )
        if not isinstance(self.pixels, np.ndarray):
            raise TypeError("content pixels must be a numpy array")
        if self.pixels.dtype != np.uint8:
            raise TypeError(
                "content pixels must be uint8, "
                f"got {self.pixels.dtype}"
            )

        bounds = self.frame.bounds_content
        channels = self.pixel_format.channel_count
        expected_shape = (
            (bounds.height, bounds.width)
            if channels == 1
            else (bounds.height, bounds.width, channels)
        )
        if self.pixels.shape != expected_shape:
            raise ValueError(
                "content pixel shape must match content bounds and pixel "
                f"format: expected {expected_shape}, got {self.pixels.shape}"
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
    def capture_info(self) -> FrameInfo:
        return self.frame.capture

    @property
    def placement(self) -> ContentPlacementInCapture:
        return self.frame.placement

    @property
    def frame_id(self) -> FrameId:
        return self.frame.capture.frame_id

    @property
    def source_id(self) -> str:
        return self.frame.capture.source_id

    @property
    def bounds_content(self) -> Rect:
        return self.frame.bounds_content

    def content_point_to_capture(self, point: Point) -> Point:
        return self.frame.content_point_to_capture(point)

    def content_rect_to_capture(self, rect: Rect) -> Rect:
        return self.frame.content_rect_to_capture(rect)


@dataclass(frozen=True, slots=True)
class ContentUnavailable:
    frame_id: FrameId
    reason: ContentFailureReason
    detail: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.frame_id, FrameId):
            raise TypeError("frame_id must be FrameId")
        if not isinstance(self.reason, ContentFailureReason):
            raise TypeError("reason must be ContentFailureReason")
        object.__setattr__(
            self,
            "detail",
            _normalize_optional_text(
                self.detail,
                field_name="content failure detail",
            ),
        )


ContentExtractionResult: TypeAlias = CapturedContent | ContentUnavailable


class ContentExtractor(Protocol):
    """Boundary that derives clean content from the current raw capture."""

    def extract(self, capture: CapturedFrame) -> ContentExtractionResult:
        ...


def extract_content(
    capture: CapturedFrame,
    *,
    extractor: ContentExtractor,
) -> ContentExtractionResult:
    if not isinstance(capture, CapturedFrame):
        raise TypeError("capture must be CapturedFrame")
    if not hasattr(extractor, "extract"):
        raise TypeError("extractor must provide extract()")
    result = extractor.extract(capture)
    if not isinstance(result, (CapturedContent, ContentUnavailable)):
        raise TypeError(
            "content extractor must return CapturedContent or "
            "ContentUnavailable"
        )
    return result


@dataclass(frozen=True, slots=True)
class IdentityContentExtractor:
    extractor_id: str = "content.identity"

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "extractor_id",
            _normalize_non_empty_text(
                self.extractor_id,
                field_name="content extractor id",
            ),
        )

    def extract(self, capture: CapturedFrame) -> ContentExtractionResult:
        return _crop_content(
            capture=capture,
            bounds_capture=capture.info.root_bounds,
            provenance=ContentExtractionProvenance(
                extractor_id=self.extractor_id,
                method=ContentExtractionMethod.IDENTITY,
            ),
        )


@dataclass(frozen=True, slots=True)
class ConfiguredContentCropExtractor:
    bounds_capture: Rect
    extractor_id: str = "content.configured_crop"

    def __post_init__(self) -> None:
        if not isinstance(self.bounds_capture, Rect):
            raise TypeError("bounds_capture must be Rect")
        object.__setattr__(
            self,
            "extractor_id",
            _normalize_non_empty_text(
                self.extractor_id,
                field_name="content extractor id",
            ),
        )

    def extract(self, capture: CapturedFrame) -> ContentExtractionResult:
        return _crop_content(
            capture=capture,
            bounds_capture=self.bounds_capture,
            provenance=ContentExtractionProvenance(
                extractor_id=self.extractor_id,
                method=ContentExtractionMethod.CONFIGURED_CROP,
            ),
        )


def _crop_content(
    *,
    capture: CapturedFrame,
    bounds_capture: Rect,
    provenance: ContentExtractionProvenance,
) -> ContentExtractionResult:
    if not isinstance(capture, CapturedFrame):
        raise TypeError("capture must be CapturedFrame")
    if not isinstance(bounds_capture, Rect):
        raise TypeError("bounds_capture must be Rect")

    if not capture.quality.usable:
        return ContentUnavailable(
            frame_id=capture.info.frame_id,
            reason=ContentFailureReason.FRAME_UNUSABLE,
        )

    capture_bounds = capture.info.root_bounds
    if not capture_bounds.contains_rect(bounds_capture):
        return ContentUnavailable(
            frame_id=capture.info.frame_id,
            reason=ContentFailureReason.BOUNDS_OUTSIDE_CAPTURE,
            detail=(
                f"content bounds {bounds_capture} are outside capture "
                f"bounds {capture_bounds}"
            ),
        )

    left = bounds_capture.left - capture_bounds.left
    top = bounds_capture.top - capture_bounds.top
    right = bounds_capture.right - capture_bounds.left
    bottom = bounds_capture.bottom - capture_bounds.top

    if capture.pixel_format.channel_count == 1:
        pixels = capture.pixels[top:bottom, left:right]
    else:
        pixels = capture.pixels[top:bottom, left:right, :]

    return CapturedContent(
        frame=ContentFrame(
            capture=capture.info,
            placement=ContentPlacementInCapture(
                bounds_capture=bounds_capture,
            ),
        ),
        pixels=pixels,
        pixel_format=capture.pixel_format,
        provenance=provenance,
    )
