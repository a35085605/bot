from __future__ import annotations

from dataclasses import dataclass, field

from geometry.point import Point
from geometry.rect import Rect
from observation import CoordinateSpace, CoordinateTransform, FrameInfo


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

    @property
    def source_bounds_capture(self) -> Rect:
        """Compatibility alias for the previous placement field name."""

        return self.bounds_capture

    @property
    def root_bounds(self) -> Rect:
        """Compatibility alias for the previous content-root name."""

        return self.bounds_content

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

    # Temporary compatibility methods. New code should use explicit
    # content/capture names instead of the ambiguous "root" vocabulary.
    def root_point_to_capture(self, point: Point) -> Point:
        return self.content_point_to_capture(point)

    def root_rect_to_capture(self, rect: Rect) -> Rect:
        return self.content_rect_to_capture(rect)

    def capture_point_to_root(self, point: Point) -> Point:
        return self.capture_point_to_content(point)

    def capture_rect_to_root(self, rect: Rect) -> Rect:
        return self.capture_rect_to_content(rect)


@dataclass(frozen=True, slots=True)
class ContentFrame:
    """Clean-content coordinate context derived from exactly one capture.

    ``capture`` retains observation identity and capture-time provenance.
    ``placement`` establishes content-space. The derived ``frame`` exists only
    as a compatibility bridge for the current world model. Execution must use
    an execution target resolver and revalidate current runtime geometry rather
    than treating the capture-time transform as an execution guarantee.
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
        capture_to_screen = self.capture.root_to_screen
        content_to_screen = CoordinateTransform(
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
                frame_id=self.capture.frame_id,
                stream_id=self.capture.stream_id,
                captured_at=self.capture.captured_at,
                root_bounds=self.bounds_content,
                source_id=self.capture.source_id,
                window=self.capture.window,
                root_to_screen=content_to_screen,
                capture_backend=self.capture.capture_backend,
            ),
        )

    @property
    def bounds_content(self) -> Rect:
        return self.placement.bounds_content

    @property
    def observation(self) -> FrameInfo:
        """Compatibility alias for the previous viewport field name."""

        return self.capture

    @property
    def root_bounds(self) -> Rect:
        """Compatibility alias for the previous content-root name."""

        return self.bounds_content

    @property
    def source_bounds_capture(self) -> Rect:
        return self.placement.bounds_capture

    def content_point_to_capture(self, point: Point) -> Point:
        return self.placement.content_point_to_capture(point)

    def content_rect_to_capture(self, rect: Rect) -> Rect:
        return self.placement.content_rect_to_capture(rect)

    def capture_point_to_content(self, point: Point) -> Point:
        return self.placement.capture_point_to_content(point)

    def capture_rect_to_content(self, rect: Rect) -> Rect:
        return self.placement.capture_rect_to_content(rect)

    # Temporary compatibility methods for downstream imports.
    def root_point_to_capture(self, point: Point) -> Point:
        return self.content_point_to_capture(point)

    def root_rect_to_capture(self, rect: Rect) -> Rect:
        return self.content_rect_to_capture(rect)

    def capture_point_to_root(self, point: Point) -> Point:
        return self.capture_point_to_content(point)

    def capture_rect_to_root(self, rect: Rect) -> Rect:
        return self.capture_rect_to_content(rect)
