from __future__ import annotations

from datetime import datetime, timezone
import unittest

import numpy as np

from content import (
    CapturedContent,
    ConfiguredContentLocator,
    ContentFailureReason,
    ContentLocationFailureReason,
    ContentRegionUnavailable,
    ContentUnavailable,
    FullFrameContentLocator,
    LocatedContentRegion,
    extract_content,
)
from geometry.point import Point
from geometry.rect import Rect
from imaging import RasterImage
from observation.capture import (
    CapturedFrame,
    CaptureQuality,
    CaptureStreamId,
    CoordinateSpace,
    CoordinateTransform,
    FrameId,
    FrameInfo,
    PixelFormat,
)


class ContentBoundaryTest(unittest.TestCase):
    def _capture(
        self,
        *,
        usable: bool = True,
        pixel_format: PixelFormat = PixelFormat.GRAY8,
    ) -> CapturedFrame:
        bounds = Rect(x=0, y=0, width=8, height=6)
        info = FrameInfo(
            frame_id=FrameId(7),
            stream_id=CaptureStreamId("session-1"),
            captured_at=datetime(
                2026,
                7,
                29,
                12,
                0,
                tzinfo=timezone.utc,
            ),
            root_bounds=bounds,
            source_id="game-window",
            surface=None,
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
            image=RasterImage(
                pixels=pixels,
                pixel_format=pixel_format,
            ),
            quality=CaptureQuality(usable=usable),
        )

    def test_full_frame_location_preserves_capture_dimensions(self) -> None:
        capture = self._capture()

        result = extract_content(
            capture,
            locator=FullFrameContentLocator(),
        )

        self.assertIsInstance(result, CapturedContent)
        assert isinstance(result, CapturedContent)
        self.assertEqual(
            result.bounds_content,
            Rect(x=0, y=0, width=8, height=6),
        )
        self.assertEqual(
            result.placement.bounds_capture,
            capture.info.root_bounds,
        )
        self.assertEqual(
            result.provenance.locator_id,
            "content.full_frame",
        )
        np.testing.assert_array_equal(result.pixels, capture.pixels)
        self.assertIs(result.image, capture.image)
        self.assertTrue(result.image.is_materialized)
        self.assertFalse(result.pixels.flags.writeable)

    def test_configured_region_establishes_content_space_without_resize(
        self,
    ) -> None:
        capture = self._capture()

        result = extract_content(
            capture,
            locator=ConfiguredContentLocator(
                bounds_capture=Rect(x=2, y=1, width=4, height=3),
            ),
        )

        self.assertIsInstance(result, CapturedContent)
        assert isinstance(result, CapturedContent)
        self.assertEqual(
            result.bounds_content,
            Rect(x=0, y=0, width=4, height=3),
        )
        self.assertEqual(result.pixels.shape, (3, 4))
        self.assertIsNot(result.image, capture.image)
        self.assertFalse(result.image.is_materialized)
        np.testing.assert_array_equal(
            result.pixels,
            capture.pixels[1:4, 2:6],
        )
        self.assertEqual(
            result.content_point_to_capture(Point(x=1, y=1)),
            Point(x=3, y=2),
        )

    def test_configured_region_preserves_multichannel_shape(self) -> None:
        result = extract_content(
            self._capture(pixel_format=PixelFormat.BGR24),
            locator=ConfiguredContentLocator(
                bounds_capture=Rect(x=1, y=2, width=5, height=3),
            ),
        )

        self.assertIsInstance(result, CapturedContent)
        assert isinstance(result, CapturedContent)
        self.assertEqual(result.pixels.shape, (3, 5, 3))

    def test_location_metadata_flows_to_captured_content(self) -> None:
        class Locator:
            def locate(self, capture: CapturedFrame) -> LocatedContentRegion:
                return LocatedContentRegion(
                    bounds_capture=Rect(x=1, y=1, width=5, height=4),
                    locator_id="content.test_locator",
                    confidence=0.75,
                )

        result = extract_content(
            self._capture(),
            locator=Locator(),
        )

        self.assertIsInstance(result, CapturedContent)
        assert isinstance(result, CapturedContent)
        self.assertEqual(
            result.provenance.locator_id,
            "content.test_locator",
        )
        self.assertEqual(result.confidence, 0.75)

    def test_unusable_capture_does_not_invoke_locator(self) -> None:
        class Locator:
            def locate(self, capture: CapturedFrame) -> object:
                raise AssertionError("locator must not be invoked")

        result = extract_content(
            self._capture(usable=False),
            locator=Locator(),
        )

        self.assertEqual(
            result,
            ContentUnavailable(
                frame_id=FrameId(7),
                reason=ContentFailureReason.FRAME_UNUSABLE,
            ),
        )

    def test_outside_region_returns_unavailable(self) -> None:
        result = extract_content(
            self._capture(),
            locator=ConfiguredContentLocator(
                bounds_capture=Rect(x=7, y=5, width=2, height=2),
            ),
        )

        self.assertIsInstance(result, ContentUnavailable)
        assert isinstance(result, ContentUnavailable)
        self.assertEqual(
            result.reason,
            ContentFailureReason.BOUNDS_OUTSIDE_CAPTURE,
        )
        self.assertIsNone(result.location_reason)

    def test_locator_failure_is_preserved(self) -> None:
        class Locator:
            def locate(
                self,
                capture: CapturedFrame,
            ) -> ContentRegionUnavailable:
                return ContentRegionUnavailable(
                    reason=ContentLocationFailureReason.AMBIGUOUS,
                    detail="two equally likely content regions",
                )

        result = extract_content(
            self._capture(),
            locator=Locator(),
        )

        self.assertEqual(
            result,
            ContentUnavailable(
                frame_id=FrameId(7),
                reason=ContentFailureReason.CONTENT_NOT_LOCATED,
                detail="two equally likely content regions",
                location_reason=ContentLocationFailureReason.AMBIGUOUS,
            ),
        )

    def test_boundary_rejects_object_without_locate(self) -> None:
        with self.assertRaises(TypeError):
            extract_content(
                self._capture(),
                locator=object(),  # type: ignore[arg-type]
            )

    def test_boundary_rejects_invalid_locator_result(self) -> None:
        class Locator:
            def locate(self, capture: CapturedFrame) -> object:
                return object()

        with self.assertRaisesRegex(
            TypeError,
            "content locator must return",
        ):
            extract_content(
                self._capture(),
                locator=Locator(),  # type: ignore[arg-type]
            )


if __name__ == "__main__":
    unittest.main()
