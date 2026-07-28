from __future__ import annotations

from content.models import ContentFrame, ContentPlacementInCapture
from geometry.point import Point
from geometry.rect import Rect
from observation import FrameInfo


class ContentPlacement(ContentPlacementInCapture):
    """Deprecated compatibility name for ``ContentPlacementInCapture``."""

    def __init__(self, source_bounds_capture: Rect) -> None:
        super().__init__(bounds_capture=source_bounds_capture)


ViewportPlacement = ContentPlacement


class CanonicalViewport(ContentFrame):
    """Deprecated compatibility wrapper for ``ContentFrame``.

    New code should import ``ContentFrame`` from ``content``. The screen mapping
    helpers remain here only for existing callers. New execution code must use
    the execution target resolver boundary and revalidate runtime geometry.
    """

    def __init__(
        self,
        observation: FrameInfo,
        placement: ContentPlacementInCapture,
    ) -> None:
        super().__init__(capture=observation, placement=placement)

    def root_point_to_screen(self, point: Point) -> Point:
        return self.frame.root_point_to_screen(point)

    def root_rect_to_screen(self, rect: Rect) -> Rect:
        return self.frame.root_rect_to_screen(rect)
