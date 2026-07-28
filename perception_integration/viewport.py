from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, TypeAlias

from content import (
    CapturedContent,
    ConfiguredContentCropExtractor,
    ContentExtractionMethod,
    ContentExtractionProvenance,
    ContentExtractionResult,
    ContentFailureReason,
    ContentUnavailable,
    IdentityContentExtractor,
)
from geometry.point import Point
from geometry.rect import Rect
from observation import CapturedFrame, FrameId, FrameInfo
from viewport import CanonicalViewport, ContentPlacement


ViewportExtractionMethod = ContentExtractionMethod
ViewportProvenance = ContentExtractionProvenance


class ViewportFailureReason(str, Enum):
    FRAME_UNUSABLE = "frame_unusable"
    SOURCE_BOUNDS_OUTSIDE_FRAME = "source_bounds_outside_frame"


@dataclass(frozen=True, slots=True)
class ViewportUnavailable:
    frame_id: FrameId
    reason: ViewportFailureReason
    detail: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.frame_id, FrameId):
            raise TypeError("frame_id must be FrameId")
        if not isinstance(self.reason, ViewportFailureReason):
            raise TypeError("reason must be ViewportFailureReason")
        if self.detail is not None:
            if not isinstance(self.detail, str):
                raise TypeError("detail must be str or None")
            normalized = self.detail.strip()
            if not normalized:
                raise ValueError("detail cannot be empty")
            object.__setattr__(self, "detail", normalized)


class PerceptionViewport(CapturedContent):
    """Deprecated compatibility wrapper for :class:`content.CapturedContent`."""

    @property
    def viewport(self) -> CanonicalViewport:
        return CanonicalViewport(
            observation=self.frame.capture,
            placement=ContentPlacement(
                source_bounds_capture=self.frame.placement.bounds_capture,
            ),
        )

    @property
    def source_info(self) -> FrameInfo:
        return self.frame.capture

    @property
    def root_bounds(self) -> Rect:
        return self.frame.bounds_content

    def root_point_to_capture(self, point: Point) -> Point:
        return self.content_point_to_capture(point)

    def root_rect_to_capture(self, rect: Rect) -> Rect:
        return self.content_rect_to_capture(rect)

    def root_point_to_screen(self, point: Point) -> Point:
        return self.viewport.root_point_to_screen(point)

    def root_rect_to_screen(self, rect: Rect) -> Rect:
        return self.viewport.root_rect_to_screen(rect)


ViewportExtractionResult: TypeAlias = (
    PerceptionViewport | ViewportUnavailable
)


class ViewportExtractor(Protocol):
    def __call__(self, frame: CapturedFrame) -> ViewportExtractionResult:
        ...


def _legacy_result(result: ContentExtractionResult) -> ViewportExtractionResult:
    if isinstance(result, CapturedContent):
        return PerceptionViewport(
            frame=result.frame,
            pixels=result.pixels,
            pixel_format=result.pixel_format,
            provenance=result.provenance,
            confidence=result.confidence,
        )

    assert isinstance(result, ContentUnavailable)
    reason = (
        ViewportFailureReason.FRAME_UNUSABLE
        if result.reason is ContentFailureReason.FRAME_UNUSABLE
        else ViewportFailureReason.SOURCE_BOUNDS_OUTSIDE_FRAME
    )
    return ViewportUnavailable(
        frame_id=result.frame_id,
        reason=reason,
        detail=result.detail,
    )


def extract_viewport(
    frame: CapturedFrame,
    *,
    extractor: ViewportExtractor,
) -> ViewportExtractionResult:
    """Deprecated compatibility boundary; use ``content.extract_content``."""

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

    def __call__(self, frame: CapturedFrame) -> ViewportExtractionResult:
        return _legacy_result(
            IdentityContentExtractor(
                extractor_id=self.extractor_id,
            ).extract(frame)
        )


@dataclass(frozen=True, slots=True)
class ConfiguredCropViewportExtractor:
    source_bounds_capture: Rect
    extractor_id: str = "viewport.configured_crop"

    def __post_init__(self) -> None:
        if not isinstance(self.source_bounds_capture, Rect):
            raise TypeError("source_bounds_capture must be Rect")

    def __call__(self, frame: CapturedFrame) -> ViewportExtractionResult:
        return _legacy_result(
            ConfiguredContentCropExtractor(
                bounds_capture=self.source_bounds_capture,
                extractor_id=self.extractor_id,
            ).extract(frame)
        )
