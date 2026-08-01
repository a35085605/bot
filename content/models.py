from __future__ import annotations

from dataclasses import dataclass, field

from geometry.point import Point
from geometry.rect import Rect
from observation.capture import (
    CaptureCoordinateMapping,
    CoordinateSpace,
    CoordinateTransform,
    FrameInfo,
)


@dataclass(frozen=True, slots=True)
class ContentPlacementInCapture:
    """Placement of clean content inside one raw capture.

    This boundary is crop-only. Content-space always begins at ``(0, 0)`` and
    preserves the selected capture rectangle's pixel dimensions. Detector ROI
    selection, resize, padding, and normalization belong to later preparation.
    """

    bounds_capture: Rect

    def __post_init__(self) -> None:
        if not isinstance(self.bounds_capture, Rect):
            raise TypeError("bounds_capture must be Rect")

    @property
    def bounds_content(self) -> Rect:
        source = self.bounds_capture
        return Rect(x=0, y=0, width=source.width, height=source.height)

    def content_point_to_capture(self, point: Point) -> Point:
        if not isinstance(point, Point):
            raise TypeError("content point must be Point")
        if not self.bounds_content.contains_point(point.x, point.y):
            raise ValueError("point must be inside content bounds")
        source = self.bounds_capture
        return Point(x=source.left + point.x, y=source.top + point.y)

    def content_rect_to_capture(self, rect: Rect) -> Rect:
        if not isinstance(rect, Rect):
            raise TypeError("content rect must be Rect")
        if not self.bounds_content.contains_rect(rect):
            raise ValueError("rect must be inside content bounds")
        source = self.bounds_capture
        return rect.translated(dx=source.left, dy=source.top)

    def capture_point_to_content(self, point: Point) -> Point:
        if not isinstance(point, Point):
            raise TypeError("capture point must be Point")
        source = self.bounds_capture
        if not source.contains_point(point.x, point.y):
            raise ValueError("point must be inside content capture bounds")
        return Point(x=point.x - source.left, y=point.y - source.top)

    def capture_rect_to_content(self, rect: Rect) -> Rect:
        if not isinstance(rect, Rect):
            raise TypeError("capture rect must be Rect")
        source = self.bounds_capture
        if not source.contains_rect(rect):
            raise ValueError("rect must be inside content capture bounds")
        return rect.translated(dx=-source.left, dy=-source.top)


def _translate_mapping_to_content(
    mapping: CaptureCoordinateMapping,
    *,
    bounds_capture: Rect,
) -> CaptureCoordinateMapping:
    transform = mapping.transform
    return CaptureCoordinateMapping(
        transform=CoordinateTransform(
            source=CoordinateSpace.ROOT,
            target=transform.target,
            scale_x=transform.scale_x,
            scale_y=transform.scale_y,
            offset_x=(
                bounds_capture.left * transform.scale_x
                + transform.offset_x
            ),
            offset_y=(
                bounds_capture.top * transform.scale_y
                + transform.offset_y
            ),
        ),
        space_id=mapping.space_id,
    )


@dataclass(frozen=True, slots=True)
class ContentFrame:
    """Clean-content coordinate context derived from exactly one capture.

    ``capture`` retains capture identity and capture-time provenance.
    ``placement`` establishes content-space. The derived ``frame`` composes the
    crop offset into every capture-time native mapping. Those mappings explain
    the historical pixels only; Execution must still revalidate current runtime
    geometry before producing a native input target.
    """

    capture: FrameInfo
    placement: ContentPlacementInCapture
    frame: FrameInfo = field(init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.capture, FrameInfo):
            raise TypeError("capture must be FrameInfo")
        if not isinstance(self.placement, ContentPlacementInCapture):
            raise TypeError("placement must be ContentPlacementInCapture")
        if not self.capture.root_bounds.contains_rect(
            self.placement.bounds_capture
        ):
            raise ValueError(
                "content capture bounds must be contained by capture bounds"
            )

        source = self.placement.bounds_capture
        screen_mapping = self.capture.mapping_to(CoordinateSpace.SCREEN)
        content_to_screen = (
            None
            if screen_mapping is None
            else _translate_mapping_to_content(
                screen_mapping,
                bounds_capture=source,
            ).transform
        )
        additional_mappings = tuple(
            _translate_mapping_to_content(
                mapping,
                bounds_capture=source,
            )
            for mapping in self.capture.additional_mappings
        )

        object.__setattr__(
            self,
            "frame",
            FrameInfo(
                frame_id=self.capture.frame_id,
                stream_id=self.capture.stream_id,
                captured_at=self.capture.captured_at,
                root_bounds=self.bounds_content,
                source_id=self.capture.source_id,
                surface=self.capture.surface,
                root_to_screen=content_to_screen,
                capture_backend_id=self.capture.capture_backend_id,
                additional_mappings=additional_mappings,
            ),
        )

    @property
    def bounds_content(self) -> Rect:
        return self.placement.bounds_content

    def content_point_to_capture(self, point: Point) -> Point:
        return self.placement.content_point_to_capture(point)

    def content_rect_to_capture(self, rect: Rect) -> Rect:
        return self.placement.content_rect_to_capture(rect)

    def capture_point_to_content(self, point: Point) -> Point:
        return self.placement.capture_point_to_content(point)

    def capture_rect_to_content(self, rect: Rect) -> Rect:
        return self.placement.capture_rect_to_content(rect)
