from __future__ import annotations

from dataclasses import dataclass, field

from geometry.point import Point
from geometry.rect import Rect
from observation import CoordinateSpace, CoordinateTransform, FrameInfo


def _ceil_div(numerator: int, denominator: int) -> int:
    return (numerator + denominator - 1) // denominator


@dataclass(frozen=True, slots=True)
class ViewportPlacement:
    """
    Spatial correspondence between canonical viewport-root and raw capture-root.

    ``root_bounds`` is the canonical coordinate space consumed by perception,
    the world model, and execution planning. ``source_bounds_capture`` is the
    raw capture-root region represented by the complete canonical viewport.

    The rectangles may have different sizes when viewport extraction also
    normalizes resolution. Leading edges round down and trailing edges round up
    so mapped half-open rectangles contain the complete source region.
    """

    source_bounds_capture: Rect
    root_bounds: Rect | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.source_bounds_capture, Rect):
            raise TypeError("source_bounds_capture must be Rect")

        root_bounds = self.root_bounds
        if root_bounds is None:
            root_bounds = Rect(
                x=0,
                y=0,
                width=self.source_bounds_capture.width,
                height=self.source_bounds_capture.height,
            )
        elif not isinstance(root_bounds, Rect):
            raise TypeError("root_bounds must be Rect or None")

        if root_bounds.left != 0 or root_bounds.top != 0:
            raise ValueError("viewport root_bounds must start at (0, 0)")

        object.__setattr__(self, "root_bounds", root_bounds)

    def root_point_to_capture(self, point: Point) -> Point:
        if not isinstance(point, Point):
            raise TypeError("viewport-root point must be Point")

        root = self._root_bounds()
        if not root.contains_point(point.x, point.y):
            raise ValueError("point must be inside viewport root bounds")

        source = self.source_bounds_capture
        return Point(
            x=source.left
            + (point.x - root.left) * source.width // root.width,
            y=source.top
            + (point.y - root.top) * source.height // root.height,
        )

    def root_rect_to_capture(self, rect: Rect) -> Rect:
        if not isinstance(rect, Rect):
            raise TypeError("viewport-root rect must be Rect")

        root = self._root_bounds()
        if not root.contains_rect(rect):
            raise ValueError("rect must be inside viewport root bounds")

        source = self.source_bounds_capture
        relative_left = rect.left - root.left
        relative_top = rect.top - root.top
        relative_right = rect.right - root.left
        relative_bottom = rect.bottom - root.top

        left = source.left + relative_left * source.width // root.width
        top = source.top + relative_top * source.height // root.height
        right = source.left + _ceil_div(
            relative_right * source.width,
            root.width,
        )
        bottom = source.top + _ceil_div(
            relative_bottom * source.height,
            root.height,
        )

        return Rect.from_ltrb(
            left=left,
            top=top,
            right=right,
            bottom=bottom,
        )

    def capture_point_to_root(self, point: Point) -> Point:
        if not isinstance(point, Point):
            raise TypeError("capture-root point must be Point")

        source = self.source_bounds_capture
        if not source.contains_point(point.x, point.y):
            raise ValueError("point must be inside viewport source bounds")

        root = self._root_bounds()
        return Point(
            x=root.left
            + (point.x - source.left) * root.width // source.width,
            y=root.top
            + (point.y - source.top) * root.height // source.height,
        )

    def capture_rect_to_root(self, rect: Rect) -> Rect:
        if not isinstance(rect, Rect):
            raise TypeError("capture-root rect must be Rect")

        source = self.source_bounds_capture
        if not source.contains_rect(rect):
            raise ValueError("rect must be inside viewport source bounds")

        root = self._root_bounds()
        relative_left = rect.left - source.left
        relative_top = rect.top - source.top
        relative_right = rect.right - source.left
        relative_bottom = rect.bottom - source.top

        left = root.left + relative_left * root.width // source.width
        top = root.top + relative_top * root.height // source.height
        right = root.left + _ceil_div(
            relative_right * root.width,
            source.width,
        )
        bottom = root.top + _ceil_div(
            relative_bottom * root.height,
            source.height,
        )

        return Rect.from_ltrb(
            left=left,
            top=top,
            right=right,
            bottom=bottom,
        )

    def _root_bounds(self) -> Rect:
        root_bounds = self.root_bounds
        assert isinstance(root_bounds, Rect)
        return root_bounds


@dataclass(frozen=True, slots=True)
class CanonicalViewport:
    """
    Shared viewport coordinate contract for capture, perception, and execution.

    ``observation`` describes the raw capture. ``placement`` maps canonical
    viewport-root coordinates into that raw capture. ``frame`` is derived from
    both and exposes viewport-root directly as a normal ``FrameInfo`` with a
    composed viewport-root-to-screen transform.

    The world model should receive ``frame`` rather than the raw observation
    frame. Execution may use the same viewport-root-to-screen mapping when it
    resolves semantic control bounds into native coordinates.
    """

    observation: FrameInfo
    placement: ViewportPlacement
    frame: FrameInfo = field(init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.observation, FrameInfo):
            raise TypeError("viewport observation must be FrameInfo")
        if not isinstance(self.placement, ViewportPlacement):
            raise TypeError("viewport placement must be ViewportPlacement")
        if not self.observation.root_bounds.contains_rect(
            self.placement.source_bounds_capture
        ):
            raise ValueError(
                "viewport source bounds must be contained by observation root"
            )

        source = self.placement.source_bounds_capture
        root = self.root_bounds
        capture_to_screen = self.observation.root_to_screen

        root_to_screen = CoordinateTransform(
            source=CoordinateSpace.ROOT,
            target=CoordinateSpace.SCREEN,
            scale_x=(
                source.width
                / root.width
                * capture_to_screen.scale_x
            ),
            scale_y=(
                source.height
                / root.height
                * capture_to_screen.scale_y
            ),
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
                root_bounds=root,
                source_id=self.observation.source_id,
                window=self.observation.window,
                root_to_screen=root_to_screen,
                capture_backend=self.observation.capture_backend,
            ),
        )

    @property
    def root_bounds(self) -> Rect:
        root_bounds = self.placement.root_bounds
        assert isinstance(root_bounds, Rect)
        return root_bounds

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
