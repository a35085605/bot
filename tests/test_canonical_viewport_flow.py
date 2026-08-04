from __future__ import annotations

from datetime import datetime, timezone
import unittest

from content import ContentFrame, ContentPlacementInCapture
from geometry.point import Point
from geometry.rect import Rect
from observation.capture import (
    CaptureStreamId,
    CoordinateSpace,
    CoordinateTransform,
    FrameId,
    FrameInfo,
)


class ContentFlowTest(unittest.TestCase):
    def _capture(self) -> FrameInfo:
        return FrameInfo(
            frame_id=FrameId(3),
            stream_id=CaptureStreamId("session-1"),
            captured_at=datetime(
                2026,
                7,
                29,
                12,
                0,
                tzinfo=timezone.utc,
            ),
            root_bounds=Rect(x=0, y=0, width=1920, height=1200),
            source_id="desktop-capture",
            surface=None,
            root_to_screen=CoordinateTransform(
                source=CoordinateSpace.ROOT,
                target=CoordinateSpace.SCREEN,
                offset_x=100,
                offset_y=200,
            ),
            capture_backend_id="test.capture",
        )

    def _content(self) -> ContentFrame:
        return ContentFrame(
            capture=self._capture(),
            placement=ContentPlacementInCapture(
                bounds_capture=Rect(
                    x=160,
                    y=120,
                    width=1600,
                    height=900,
                ),
            ),
        )

    def test_content_frame_establishes_zero_based_bounds(self) -> None:
        content = self._content()

        self.assertEqual(
            content.bounds_content,
            Rect(x=0, y=0, width=1600, height=900),
        )
        self.assertEqual(content.frame.root_bounds, content.bounds_content)
        self.assertNotEqual(
            content.frame.root_bounds,
            content.capture.root_bounds,
        )

    def test_content_coordinates_map_back_to_capture(self) -> None:
        content = self._content()

        self.assertEqual(
            content.content_point_to_capture(Point(x=40, y=30)),
            Point(x=200, y=150),
        )
        self.assertEqual(
            content.capture_point_to_content(Point(x=200, y=150)),
            Point(x=40, y=30),
        )

    def test_content_frame_composes_capture_time_screen_mapping(self) -> None:
        content = self._content()
        mapping = content.frame.root_to_screen

        self.assertIsNotNone(mapping)
        assert mapping is not None
        self.assertEqual(mapping.offset_x, 260)
        self.assertEqual(mapping.offset_y, 320)

    def test_content_rejects_bounds_outside_capture(self) -> None:
        with self.assertRaises(ValueError):
            ContentFrame(
                capture=self._capture(),
                placement=ContentPlacementInCapture(
                    bounds_capture=Rect(
                        x=1800,
                        y=1100,
                        width=200,
                        height=200,
                    ),
                ),
            )


if __name__ == "__main__":
    unittest.main()
