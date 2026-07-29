from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
import unittest

import numpy as np

from capture import (
    AcquiredFrame,
    CapturedFrame,
    CaptureQuality,
    CaptureStreamId,
    CaptureSurface,
    CoordinateSpace,
    CoordinateTransform,
    FrameId,
    FrameInfo,
    MaterializingFrameSource,
    PixelFormat,
    materialize_capture,
)
from geometry.point import Point
from geometry.rect import Rect
from imaging import RasterImage, crop_image


class CaptureTest(unittest.TestCase):
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
            surface=CaptureSurface(
                surface_id=" hwnd:42 ",
                client_bounds_screen=Rect(
                    x=200,
                    y=300,
                    width=200,
                    height=100,
                ),
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

    def test_frame_contract_normalizes_identity_and_surface(self) -> None:
        info = self._frame_info()

        self.assertEqual(info.stream_id.value, "session-1")
        self.assertEqual(info.source_id, "game-window")
        self.assertIsNotNone(info.surface)
        assert info.surface is not None
        self.assertEqual(info.surface.surface_id, "hwnd:42")
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

    def test_frame_can_describe_desktop_capture_without_surface(self) -> None:
        info = FrameInfo(
            frame_id=FrameId(1),
            stream_id=CaptureStreamId("session-1"),
            captured_at=datetime.now(timezone.utc),
            root_bounds=Rect(x=0, y=0, width=1920, height=1080),
            source_id="desktop-1",
            surface=None,
            root_to_screen=CoordinateTransform(
                source=CoordinateSpace.ROOT,
                target=CoordinateSpace.SCREEN,
                offset_x=-1920,
            ),
            capture_backend="test.desktop",
        )

        self.assertIsNone(info.surface)
        self.assertEqual(
            info.capture_bounds_screen,
            Rect(x=-1920, y=0, width=1920, height=1080),
        )

    def test_capture_surface_validates_geometry_only(self) -> None:
        surface = CaptureSurface(
            surface_id="hwnd:42",
            client_bounds_screen=Rect(x=10, y=10, width=80, height=80),
            outer_bounds_screen=Rect(x=0, y=0, width=100, height=100),
        )

        self.assertFalse(hasattr(surface, "title"))
        self.assertFalse(hasattr(surface, "process_id"))
        self.assertFalse(hasattr(surface, "is_foreground"))
        self.assertFalse(hasattr(surface, "is_minimized"))

    def test_capture_surface_rejects_inconsistent_bounds(self) -> None:
        with self.assertRaises(ValueError):
            CaptureSurface(
                surface_id="hwnd:42",
                client_bounds_screen=Rect(
                    x=0,
                    y=0,
                    width=100,
                    height=100,
                ),
                outer_bounds_screen=Rect(
                    x=10,
                    y=10,
                    width=20,
                    height=20,
                ),
            )

    def test_captured_frame_owns_immutable_pixels(self) -> None:
        source = np.arange(5000, dtype=np.uint8).reshape(50, 100)
        frame = CapturedFrame(
            info=self._frame_info(),
            image=RasterImage(
                pixels=source,
                pixel_format=PixelFormat.GRAY8,
            ),
            quality=CaptureQuality(usable=True, sharpness=0.9),
        )

        source[0, 0] = 99

        self.assertEqual(int(frame.pixels[0, 0]), 0)
        self.assertFalse(frame.pixels.flags.writeable)
        with self.assertRaises(ValueError):
            frame.pixels.setflags(write=True)
        with self.assertRaises(FrozenInstanceError):
            frame.quality = CaptureQuality(usable=False)

    def test_captured_frame_rejects_logical_crop(self) -> None:
        root = RasterImage(
            pixels=np.arange(52 * 102, dtype=np.uint8).reshape(52, 102),
            pixel_format=PixelFormat.GRAY8,
        )
        cropped = crop_image(
            root,
            bounds=Rect(x=1, y=1, width=100, height=50),
        )

        with self.assertRaisesRegex(
            ValueError,
            "must own independent contiguous storage",
        ):
            CapturedFrame(
                info=self._frame_info(),
                image=cropped,
                quality=CaptureQuality(usable=True),
            )

    def test_materialize_capture_crosses_ownership_boundary(self) -> None:
        root = RasterImage(
            pixels=np.arange(52 * 102, dtype=np.uint8).reshape(52, 102),
            pixel_format=PixelFormat.GRAY8,
        )
        cropped = crop_image(
            root,
            bounds=Rect(x=1, y=1, width=100, height=50),
        )
        acquired = AcquiredFrame(
            info=self._frame_info(),
            image=cropped,
            quality=CaptureQuality(usable=True),
        )

        frame = materialize_capture(acquired)

        self.assertTrue(frame.image.is_materialized)
        self.assertTrue(frame.image.is_contiguous)
        self.assertFalse(np.shares_memory(frame.pixels, root.pixels))
        np.testing.assert_array_equal(frame.pixels, cropped.pixels)

    def test_materializing_frame_source_normalizes_backend_output(self) -> None:
        root = RasterImage(
            pixels=np.arange(52 * 102, dtype=np.uint8).reshape(52, 102),
            pixel_format=PixelFormat.GRAY8,
        )
        cropped = crop_image(
            root,
            bounds=Rect(x=1, y=1, width=100, height=50),
        )
        acquired = AcquiredFrame(
            info=self._frame_info(),
            image=cropped,
            quality=CaptureQuality(usable=True),
        )

        class Backend:
            def capture(self) -> AcquiredFrame:
                return acquired

        frame = MaterializingFrameSource(backend=Backend()).capture()

        self.assertIsInstance(frame, CapturedFrame)
        self.assertTrue(frame.image.is_materialized)
        self.assertFalse(np.shares_memory(frame.pixels, root.pixels))

    def test_materializing_frame_source_rejects_invalid_backend_result(
        self,
    ) -> None:
        class Backend:
            def capture(self) -> object:
                return object()

        with self.assertRaisesRegex(
            TypeError,
            "must return AcquiredFrame",
        ):
            MaterializingFrameSource(backend=Backend()).capture()

    def test_captured_frame_validates_image_size(self) -> None:
        with self.assertRaises(ValueError):
            CapturedFrame(
                info=self._frame_info(),
                image=RasterImage(
                    pixels=np.zeros((49, 100, 3), dtype=np.uint8),
                    pixel_format=PixelFormat.BGR24,
                ),
                quality=CaptureQuality(usable=True),
            )

    def test_quality_describes_pixels_not_window_occlusion(self) -> None:
        quality = CaptureQuality(
            usable=False,
            contaminated=True,
            detail="desktop pixels overlap the requested capture region",
        )

        self.assertTrue(quality.contaminated)
        self.assertFalse(hasattr(quality, "occluded"))


if __name__ == "__main__":
    unittest.main()
