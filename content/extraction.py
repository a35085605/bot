from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from numbers import Real
from typing import Protocol, TypeAlias

from content.models import ContentFrame, ContentPlacementInCapture
from geometry.point import Point
from geometry.rect import Rect
from imaging import ImagePixels, PixelFormat, RasterImage, crop_image
from observation import (
    CapturedFrame,
    FrameId,
    FrameInfo,
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


class ContentLocationFailureReason(str, Enum):
    NOT_FOUND = "not_found"
    AMBIGUOUS = "ambiguous"
    UNSUPPORTED_LAYOUT = "unsupported_layout"


class ContentFailureReason(str, Enum):
    FRAME_UNUSABLE = "frame_unusable"
    CONTENT_NOT_LOCATED = "content_not_located"
    BOUNDS_OUTSIDE_CAPTURE = "bounds_outside_capture"


@dataclass(frozen=True, slots=True)
class ContentExtractionProvenance:
    locator_id: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "locator_id",
            _normalize_non_empty_text(
                self.locator_id,
                field_name="content locator id",
            ),
        )


@dataclass(frozen=True, slots=True)
class LocatedContentRegion:
    """Capture-space content region selected by one locator."""

    bounds_capture: Rect
    locator_id: str
    confidence: float = 1.0

    def __post_init__(self) -> None:
        if not isinstance(self.bounds_capture, Rect):
            raise TypeError("bounds_capture must be Rect")
        object.__setattr__(
            self,
            "locator_id",
            _normalize_non_empty_text(
                self.locator_id,
                field_name="content locator id",
            ),
        )
        object.__setattr__(
            self,
            "confidence",
            _normalize_confidence(self.confidence),
        )


@dataclass(frozen=True, slots=True)
class ContentRegionUnavailable:
    reason: ContentLocationFailureReason
    detail: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.reason, ContentLocationFailureReason):
            raise TypeError(
                "reason must be ContentLocationFailureReason"
            )
        object.__setattr__(
            self,
            "detail",
            _normalize_optional_text(
                self.detail,
                field_name="content location failure detail",
            ),
        )


ContentRegionResult: TypeAlias = (
    LocatedContentRegion | ContentRegionUnavailable
)


class ContentRegionLocator(Protocol):
    """Locate clean content inside the current raw capture."""

    def locate(self, capture: CapturedFrame) -> ContentRegionResult:
        ...


@dataclass(frozen=True, slots=True)
class CapturedContent:
    """Clean raster and content-space context derived from one capture."""

    frame: ContentFrame
    image: RasterImage
    provenance: ContentExtractionProvenance
    confidence: float = 1.0

    def __post_init__(self) -> None:
        if not isinstance(self.frame, ContentFrame):
            raise TypeError("frame must be ContentFrame")
        if not isinstance(self.image, RasterImage):
            raise TypeError("content image must be RasterImage")
        if not isinstance(self.provenance, ContentExtractionProvenance):
            raise TypeError(
                "provenance must be ContentExtractionProvenance"
            )

        bounds = self.frame.bounds_content
        if (
            self.image.width != bounds.width
            or self.image.height != bounds.height
        ):
            raise ValueError(
                "content image size must match content bounds: "
                f"expected {bounds.width}x{bounds.height}, "
                f"got {self.image.width}x{self.image.height}"
            )

        object.__setattr__(
            self,
            "confidence",
            _normalize_confidence(self.confidence),
        )

    @property
    def pixels(self) -> ImagePixels:
        return self.image.pixels

    @property
    def pixel_format(self) -> PixelFormat:
        return self.image.pixel_format

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
    location_reason: ContentLocationFailureReason | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.frame_id, FrameId):
            raise TypeError("frame_id must be FrameId")
        if not isinstance(self.reason, ContentFailureReason):
            raise TypeError("reason must be ContentFailureReason")
        if self.location_reason is not None and not isinstance(
            self.location_reason,
            ContentLocationFailureReason,
        ):
            raise TypeError(
                "location_reason must be "
                "ContentLocationFailureReason or None"
            )
        if self.reason is ContentFailureReason.CONTENT_NOT_LOCATED:
            if self.location_reason is None:
                raise ValueError(
                    "content_not_located requires location_reason"
                )
        elif self.location_reason is not None:
            raise ValueError(
                "location_reason is only valid for content_not_located"
            )
        object.__setattr__(
            self,
            "detail",
            _normalize_optional_text(
                self.detail,
                field_name="content failure detail",
            ),
        )


ContentExtractionResult: TypeAlias = CapturedContent | ContentUnavailable


def extract_content(
    capture: CapturedFrame,
    *,
    locator: ContentRegionLocator,
) -> ContentExtractionResult:
    """Locate and derive clean content from one captured frame."""

    if not isinstance(capture, CapturedFrame):
        raise TypeError("capture must be CapturedFrame")
    if not hasattr(locator, "locate"):
        raise TypeError("locator must provide locate()")

    if not capture.quality.usable:
        return ContentUnavailable(
            frame_id=capture.info.frame_id,
            reason=ContentFailureReason.FRAME_UNUSABLE,
        )

    located = locator.locate(capture)
    if isinstance(located, ContentRegionUnavailable):
        return ContentUnavailable(
            frame_id=capture.info.frame_id,
            reason=ContentFailureReason.CONTENT_NOT_LOCATED,
            detail=located.detail,
            location_reason=located.reason,
        )
    if not isinstance(located, LocatedContentRegion):
        raise TypeError(
            "content locator must return LocatedContentRegion or "
            "ContentRegionUnavailable"
        )

    bounds_capture = located.bounds_capture
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

    image = capture.image
    if bounds_capture != capture_bounds:
        image = crop_image(
            capture.image,
            bounds=bounds_capture.translated(
                dx=-capture_bounds.left,
                dy=-capture_bounds.top,
            ),
        )

    return CapturedContent(
        frame=ContentFrame(
            capture=capture.info,
            placement=ContentPlacementInCapture(
                bounds_capture=bounds_capture,
            ),
        ),
        image=image,
        provenance=ContentExtractionProvenance(
            locator_id=located.locator_id,
        ),
        confidence=located.confidence,
    )


@dataclass(frozen=True, slots=True)
class FullFrameContentLocator:
    locator_id: str = "content.full_frame"

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "locator_id",
            _normalize_non_empty_text(
                self.locator_id,
                field_name="content locator id",
            ),
        )

    def locate(self, capture: CapturedFrame) -> ContentRegionResult:
        if not isinstance(capture, CapturedFrame):
            raise TypeError("capture must be CapturedFrame")
        return LocatedContentRegion(
            bounds_capture=capture.info.root_bounds,
            locator_id=self.locator_id,
        )


@dataclass(frozen=True, slots=True)
class ConfiguredContentLocator:
    bounds_capture: Rect
    locator_id: str = "content.configured"

    def __post_init__(self) -> None:
        if not isinstance(self.bounds_capture, Rect):
            raise TypeError("bounds_capture must be Rect")
        object.__setattr__(
            self,
            "locator_id",
            _normalize_non_empty_text(
                self.locator_id,
                field_name="content locator id",
            ),
        )

    def locate(self, capture: CapturedFrame) -> ContentRegionResult:
        if not isinstance(capture, CapturedFrame):
            raise TypeError("capture must be CapturedFrame")
        return LocatedContentRegion(
            bounds_capture=self.bounds_capture,
            locator_id=self.locator_id,
        )
