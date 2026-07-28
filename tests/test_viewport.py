from __future__ import annotations

from datetime import datetime, timezone
import unittest

from geometry.point import Point
from geometry.rect import Rect
from observation import (
    CaptureStreamId,
    CoordinateSpace,
    CoordinateTransform,
    FrameId,
    FrameInfo,
    WindowContext,
)
from viewport import CanonicalViewport, ContentPlacement


class CanonicalViewportTest(unittest.TestCase):
    def _observation(self) -> FrameInfo:
        return FrameInfo(
            frame_id=FrameId(7),
            stream_id=CaptureStreamId("session-1"),
            captured_at=datetime(
                2026,
                7,
                28,
                12,
                0,
                tzinfo=timezone.utc,
            ),
            root_bounds=Rect(x=0, y=0, width=1920, height=1200),
            source_id="game-window",
            window=WindowContext(
                window_id="hwnd:42",
                client_bounds_screen=Rect(
                    x=100,
                    y=200,
                    width=1920,
                    height=1200,
                ),
            ),
            root_to_screen=CoordinateTransform(
                source=CoordinateSpace.ROOT,
                target=CoordinateSpace.SCREEN,
                offset_x=100,
                offset_y=200,
            ),
            capture_backend="test.capture",
        )

    def test_crop_establishes_content_root_and_screen_mapping(self) -> None:
        viewport = CanonicalViewport(
            observation=self._observation(),
            placement=ContentPlacement(
                source_bounds_capture=Rect(
                    x=160,
                    y=120,
                    width=1600,
                    height=900,
                ),
            ),
        )

        self.assertEqual(
            viewport.root_bounds,
            Rect(x=0, y=0, width=1600, height=900),
        )
        self.assertEqual(viewport.frame.root_bounds, viewport.root_bounds)
        self.assertEqual(
            viewport.root_point_to_capture(Point(x=10, y=20)),
            Point(x=170, y=140),
        )
        self.assertEqual(
            viewport.root_point_to_screen(Point(x=10, y=20)),
            Point(x=270, y=340),
        )
        self.assertEqual(
            viewport.root_rect_to_screen(
                Rect(x=10, y=20, width=30, height=40)
            ),
            Rect(x=270, y=340, width=30, height=40),
        )

    def test_content_placement_preserves_capture_crop_dimensions(self) -> None:
        placement = ContentPlacement(
            source_bounds_capture=Rect(
                x=160,
                y=120,
                width=1600,
                height=900,
            )
        )

        self.assertEqual(
            placement.root_bounds,
            Rect(x=0, y=0, width=1600, height=900),
        )
        root_rect = Rect(x=192, y=108, width=384, height=216)
        capture_rect = placement.root_rect_to_capture(root_rect)
        self.assertEqual(
            capture_rect,
            Rect(x=352, y=228, width=384, height=216),
        )
        self.assertEqual(placement.capture_rect_to_root(capture_rect), root_rect)

    def test_content_placement_does_not_accept_normalized_root_bounds(self) -> None:
        with self.assertRaises(TypeError):
            ContentPlacement(  # type: ignore[call-arg]
                source_bounds_capture=Rect(
                    x=0,
                    y=0,
                    width=100,
                    height=100,
                ),
                root_bounds=Rect(
                    x=0,
                    y=0,
                    width=200,
                    height=200,
                ),
            )

    def test_rejects_source_outside_observation(self) -> None:
        with self.assertRaises(ValueError):
            CanonicalViewport(
                observation=self._observation(),
                placement=ContentPlacement(
                    source_bounds_capture=Rect(
                        x=1800,
                        y=1100,
                        width=200,
                        height=200,
                    ),
                ),
            )


if __name__ == "__main__":
    unittest.main()
