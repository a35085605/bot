from __future__ import annotations

from dataclasses import dataclass, field

from geometry.point import Point
from geometry.rect import Rect
from observation import CoordinateSpace, CoordinateTransform, FrameInfo


@dataclass(frozen=True, slots=True)
class ContentPlacement:
    """Placement of clean captured content inside one raw capture.

    ``source_bounds_capture`` is the raw capture-root rectangle represented by
    the clean content. Content-root always begins at ``(0, 0)`` and preserves
    the source rectangle's pixel dimensions. This boundary therefore expresses
    crop/translation only; resizing and normalization belong to later detector
    input preparation.
    """

    source_bounds_capture: Rect

    def __post_init__(self) -> None:
        if not isinstance(self.source_bounds_capture, Rect):
            raise TypeError("source_bounds_capture must be Rect")

    @property
    def root_bounds(self) -> Rect:
        source = self.source_bounds_capture
        return Rect(x=0, y=0, width=source.width, height=source.height)

    def root_point_to_capture(self, point: Point) -> Point:
        if not isinstance(point, Point):
            raise TypeError("content-root point must be Point")
        if not self.root_bounds.contains_point(point.x, point.y):
            raise ValueError("point must be inside content root bounds")

        source = self.source_bounds_capture
        return Point(x=source.left + point.x, y=source.top + point.y)

    def root_rect_to_capture(self, rect: Rect) -> Rect:
        if not isinstance(rect, Rect):
            raise TypeError("content-root rect must be Rect")
        if not self.root_bounds.contains_rect(rect):
            raise ValueError("rect must be inside content root bounds")

        source = self.source_bounds_capture
        return rect.translated(dx=source.left, dy=source.top)

    def capture_point_to_root(self, point: Point) -> Point:
        if not isinstance(point, Point):
            raise TypeError("capture-root point must be Point")

        source = self.source_bounds_capture
        if not source.contains_point(point.x, point.y):
            raise ValueError("point must be inside content source bounds")

        return Point(x=point.x - source.left, y=point.y - source.top)

    def capture_rect_to_root(self, rect: Rect) -> Rect:
        if not isinstance(rect, Rect):
            raise TypeError("capture-root rect must be Rect")

        source = self.source_bounds_capture
        if not source.contains_rect(rect):
            raise ValueError("rect must be inside content source bounds")

        return rect.translated(dx=-source.left, dy=-source.top)


# Temporary compatibility alias for downstream imports. The model itself is
# intentionally crop-only and no longer accepts an independent root size.
ViewportPlacement = ContentPlacement


@dataclass(frozen=True, slots=True)
class CanonicalViewport:
    """Shared clean-content coordinate contract.

    ``observation`` describes the raw capture. ``placement`` identifies the
    clean raw-capture region and establishes a zero-origin content-root with the
    same pixel dimensions. ``frame`` exposes that content-root as a normal
    ``FrameInfo`` with a composed content-root-to-screen transform.
    """

    observation: FrameInfo
    placement: ContentPlacement
    frame: FrameInfo = field(init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.observation, FrameInfo):
            raise TypeError("viewport observation must be FrameInfo")
        if not isinstance(self.placement, ContentPlacement):
            raise TypeError("viewport placement must be ContentPlacement")
        if not self.observation.root_bounds.contains_rect(
            self.placement.source_bounds_capture
        ):
            raise ValueError(
                "viewport source bounds must be contained by observation root"
            )

        source = self.placement.source_bounds_capture
        capture_to_screen = self.observation.root_to_screen
        root_to_screen = CoordinateTransform(
            source=CoordinateSpace.ROOT,
            target=CoordinateSpace.SCREEN,
            scale_x=capture_to_screen.scale_x,
            scale_y=capture_to_screen.scale_y,
            offset_x=(
                source.left * capture_to_screen.scale_x
                + capture_to_screen.offset_x
            ),
            offset_y=(
                source.top * capture_to_screen.scale_y
                + capture_to_screen.offset_y
            ),
        )

        object.__setattr__(
            self,
            "frame",
            FrameInfo(
                frame_id=self.observation.frame_id,
                stream_id=self.observation.stream_id,
                captured_at=self.observation.captured_at,
                root_bounds=self.root_bounds,
                source_id=self.observation.source_id,
                window=self.observation.window,
                root_to_screen=root_to_screen,
                capture_backend=self.observation.capture_backend,
            ),
        )

    @property
    def root_bounds(self) -> Rect:
        return self.placement.root_bounds

    @property
    def source_bounds_capture(self) -> Rect:
        return self.placement.source_bounds_capture

    def root_point_to_capture(self, point: Point) -> Point:
        return self.placement.root_point_to_capture(point)

    def root_rect_to_capture(self, rect: Rect) -> Rect:
        return self.placement.root_rect_to_capture(rect)

    def capture_point_to_root(self, point: Point) -> Point:
        return self.placement.capture_point_to_root(point)

    def capture_rect_to_root(self, rect: Rect) -> Rect:
        return self.placement.capture_rect_to_root(rect)

    def root_point_to_screen(self, point: Point) -> Point:
        return self.frame.root_point_to_screen(point)

    def root_rect_to_screen(self, rect: Rect) -> Rect:
        return self.frame.root_rect_to_screen(rect)
