from __future__ import annotations

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
from perception_integration import (
    ConfiguredCropViewportExtractor,
    IdentityViewportExtractor,
    PerceptionViewport,
    ViewportExtractionMethod,
    ViewportFailureReason,
    ViewportUnavailable,
    extract_viewport,
)


class PerceptionViewportTest(unittest.TestCase):
    def _frame(
        self,
        *,
        usable: bool = True,
        pixel_format: PixelFormat = PixelFormat.GRAY8,
    ) -> CapturedFrame:
        root_bounds = Rect(x=0, y=0, width=8, height=6)
        info = FrameInfo(
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
            root_bounds=root_bounds,
            source_id="game-window",
            window=WindowContext(
                window_id="hwnd:42",
                client_bounds_screen=Rect(
                    x=100,
                    y=200,
                    width=8,
                    height=6,
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

        if pixel_format is PixelFormat.GRAY8:
            pixels = np.arange(48, dtype=np.uint8).reshape(6, 8)
        else:
            pixels = np.arange(
                6 * 8 * pixel_format.channel_count,
                dtype=np.uint8,
            ).reshape(6, 8, pixel_format.channel_count)

        return CapturedFrame(
            info=info,
            pixels=pixels,
            pixel_format=pixel_format,
            quality=CaptureQuality(usable=usable),
        )

    def test_identity_extraction_establishes_viewport_root(self) -> None:
        frame = self._frame()

        result = extract_viewport(
            frame,
            extractor=IdentityViewportExtractor(),
        )

        self.assertIsInstance(result, PerceptionViewport)
        assert isinstance(result, PerceptionViewport)
        self.assertEqual(result.frame_id, frame.info.frame_id)
        self.assertEqual(result.source_id, frame.info.source_id)
        self.assertEqual(result.root_bounds, Rect(x=0, y=0, width=8, height=6))
        self.assertEqual(
            result.placement.source_bounds_capture,
            frame.info.root_bounds,
        )
        self.assertEqual(
            result.provenance.method,
            ViewportExtractionMethod.IDENTITY,
        )
        np.testing.assert_array_equal(result.pixels, frame.pixels)
        self.assertFalse(result.pixels.flags.writeable)

    def test_configured_crop_removes_outer_capture_pixels(self) -> None:
        frame = self._frame()
        source_bounds = Rect(x=2, y=1, width=4, height=3)

        result = extract_viewport(
            frame,
            extractor=ConfiguredCropViewportExtractor(source_bounds),
        )

        self.assertIsInstance(result, PerceptionViewport)
        assert isinstance(result, PerceptionViewport)
        self.assertEqual(result.root_bounds, Rect(x=0, y=0, width=4, height=3))
        self.assertEqual(
            result.provenance.method,
            ViewportExtractionMethod.CONFIGURED_CROP,
        )
        np.testing.assert_array_equal(
            result.pixels,
            frame.pixels[1:4, 2:6],
        )
        self.assertEqual(
            result.root_point_to_capture(Point(x=1, y=1)),
            Point(x=3, y=2),
        )
        self.assertEqual(
            result.root_point_to_screen(Point(x=1, y=1)),
            Point(x=103, y=202),
        )
        self.assertEqual(
            result.root_rect_to_screen(
                Rect(x=1, y=1, width=2, height=1)
            ),
            Rect(x=103, y=202, width=2, height=1),
        )

    def test_crop_preserves_multichannel_pixel_shape(self) -> None:
        frame = self._frame(pixel_format=PixelFormat.BGR24)

        result = extract_viewport(
            frame,
            extractor=ConfiguredCropViewportExtractor(
                Rect(x=1, y=2, width=5, height=3)
            ),
        )

        self.assertIsInstance(result, PerceptionViewport)
        assert isinstance(result, PerceptionViewport)
        self.assertEqual(result.pixels.shape, (3, 5, 3))
        np.testing.assert_array_equal(
            result.pixels,
            frame.pixels[2:5, 1:6, :],
        )

    def test_unusable_capture_does_not_enter_perception(self) -> None:
        result = extract_viewport(
            self._frame(usable=False),
            extractor=IdentityViewportExtractor(),
        )

        self.assertEqual(
            result,
            ViewportUnavailable(
                frame_id=FrameId(7),
                reason=ViewportFailureReason.FRAME_UNUSABLE,
            ),
        )

    def test_crop_outside_capture_returns_unavailable(self) -> None:
        result = extract_viewport(
            self._frame(),
            extractor=ConfiguredCropViewportExtractor(
                Rect(x=7, y=5, width=2, height=2)
            ),
        )

        self.assertIsInstance(result, ViewportUnavailable)
        assert isinstance(result, ViewportUnavailable)
        self.assertEqual(
            result.reason,
            ViewportFailureReason.SOURCE_BOUNDS_OUTSIDE_FRAME,
        )
        self.assertIsNotNone(result.detail)

    def test_boundary_rejects_invalid_extractor_result(self) -> None:
        with self.assertRaises(TypeError):
            extract_viewport(
                self._frame(),
                extractor=lambda frame: object(),  # type: ignore[arg-type]
            )


if __name__ == "__main__":
    unittest.main()
