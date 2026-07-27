from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
import unittest

import numpy as np

from geometry.point import Point
from geometry.rect import Rect
from observation import (
    CapturedFrame,
    CaptureQuality,
    CaptureStreamId,
    CoordinateSpace,
    CoordinateTransform,
    FrameId,
    FrameInfo,
    PixelFormat,
    WindowContext,
)


class ObservationTest(unittest.TestCase):
    def _frame_info(self) -> FrameInfo:
        return FrameInfo(
            frame_id=FrameId(7),
            stream_id=CaptureStreamId(" session-1 "),
            captured_at=datetime(
                2026,
                7,
                27,
                12,
                0,
                tzinfo=timezone.utc,
            ),
            root_bounds=Rect(x=0, y=0, width=100, height=50),
            source_id=" game-window ",
            window=WindowContext(
                window_id=" hwnd:42 ",
                client_bounds_screen=Rect(
                    x=200,
                    y=300,
                    width=200,
                    height=100,
                ),
                process_id=1234,
                title=" Example Game ",
                is_foreground=True,
            ),
            root_to_screen=CoordinateTransform(
                source=CoordinateSpace.ROOT,
                target=CoordinateSpace.SCREEN,
                scale_x=2,
                scale_y=2,
                offset_x=200,
                offset_y=300,
            ),
            capture_backend=" dxgi ",
        )

    def test_frame_contract_normalizes_identity_and_context(self) -> None:
        info = self._frame_info()

        self.assertEqual(info.stream_id.value, "session-1")
        self.assertEqual(info.source_id, "game-window")
        self.assertEqual(info.window.window_id, "hwnd:42")
        self.assertEqual(info.window.title, "Example Game")
        self.assertEqual(info.capture_backend, "dxgi")
        self.assertEqual(
            info.capture_bounds_screen,
            Rect(x=200, y=300, width=200, height=100),
        )

    def test_coordinate_transform_maps_root_geometry(self) -> None:
        info = self._frame_info()

        self.assertEqual(
            info.root_point_to_screen(Point(x=10, y=20)),
            Point(x=220, y=340),
        )
        self.assertEqual(
            info.root_rect_to_screen(
                Rect(x=10, y=5, width=20, height=10)
            ),
            Rect(x=220, y=310, width=40, height=20),
        )
        self.assertEqual(
            info.root_to_screen.inverse().point(Point(x=220, y=340)),
            Point(x=10, y=20),
        )

    def test_frame_requires_capture_inside_window_client(self) -> None:
        with self.assertRaises(ValueError):
            FrameInfo(
                frame_id=FrameId(1),
                stream_id=CaptureStreamId("session-1"),
                captured_at=datetime.now(timezone.utc),
                root_bounds=Rect(x=0, y=0, width=100, height=100),
                source_id="game-window",
                window=WindowContext(
                    window_id="hwnd:42",
                    client_bounds_screen=Rect(
                        x=0,
                        y=0,
                        width=50,
                        height=50,
                    ),
                ),
                root_to_screen=CoordinateTransform(
                    source=CoordinateSpace.ROOT,
                    target=CoordinateSpace.SCREEN,
                ),
                capture_backend="test.capture",
            )

    def test_captured_frame_owns_immutable_pixels(self) -> None:
        source = np.arange(5000, dtype=np.uint8).reshape(50, 100)
        frame = CapturedFrame(
            info=self._frame_info(),
            pixels=source,
            pixel_format=PixelFormat.GRAY8,
            quality=CaptureQuality(usable=True, sharpness=0.9),
        )

        source[0, 0] = 99

        self.assertEqual(int(frame.pixels[0, 0]), 0)
        self.assertFalse(frame.pixels.flags.writeable)
        with self.assertRaises(ValueError):
            frame.pixels.setflags(write=True)
        with self.assertRaises(FrozenInstanceError):
            frame.quality = CaptureQuality(usable=False)

    def test_captured_frame_validates_pixel_format_shape(self) -> None:
        with self.assertRaises(ValueError):
            CapturedFrame(
                info=self._frame_info(),
                pixels=np.zeros((50, 100, 3), dtype=np.uint8),
                pixel_format=PixelFormat.BGRA32,
                quality=CaptureQuality(usable=True),
            )

    def test_window_context_rejects_impossible_state(self) -> None:
        with self.assertRaises(ValueError):
            WindowContext(
                window_id="hwnd:42",
                client_bounds_screen=Rect(
                    x=0,
                    y=0,
                    width=100,
                    height=100,
                ),
                is_foreground=True,
                is_minimized=True,
            )


if __name__ == "__main__":
    unittest.main()
