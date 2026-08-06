from __future__ import annotations

from datetime import datetime, timedelta, timezone
import unittest

import numpy as np

from geometry.rect import Rect
from imaging import RasterImage
from observation import ObservationBundle
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
from observation.target_runtime import (
    TargetAvailability,
    TargetRuntimeSnapshot,
)
from observation.temporal import TemporalSnapshot
from target import TargetId


class ObservationTest(unittest.TestCase):
    def _capture(self, captured_at: datetime) -> CapturedFrame:
        return CapturedFrame(
            info=FrameInfo(
                frame_id=FrameId(1),
                stream_id=CaptureStreamId("stream-1"),
                captured_at=captured_at,
                root_bounds=Rect(x=0, y=0, width=4, height=3),
                source_id="source-1",
                surface=None,
                root_to_screen=CoordinateTransform(
                    source=CoordinateSpace.ROOT,
                    target=CoordinateSpace.SCREEN,
                ),
                capture_backend_id="test.capture",
            ),
            image=RasterImage(
                pixels=np.zeros((3, 4), dtype=np.uint8),
                pixel_format=PixelFormat.GRAY8,
            ),
            quality=CaptureQuality(usable=True),
        )

    def test_bundle_preserves_independent_observation_times(self) -> None:
        reference = datetime(2026, 7, 29, 10, 0, 1, tzinfo=timezone.utc)
        bundle = ObservationBundle(
            cycle_id=" cycle-1 ",
            temporal=TemporalSnapshot(
                observed_at=reference,
                monotonic_seconds=100.0,
                observer_id="test.clock",
            ),
            capture=self._capture(reference - timedelta(seconds=1)),
            runtime=TargetRuntimeSnapshot(
                target_id=TargetId("target-1"),
                observed_at=reference - timedelta(milliseconds=300),
                availability=TargetAvailability.AVAILABLE,
                inspector_id="test.runtime",
            ),
        )

        self.assertEqual(bundle.cycle_id, "cycle-1")
        self.assertEqual(
            bundle.coherence.capture_skew,
            timedelta(seconds=1),
        )
        self.assertEqual(
            bundle.coherence.runtime_skew,
            timedelta(milliseconds=300),
        )
        self.assertEqual(
            bundle.coherence.maximum_skew,
            timedelta(seconds=1),
        )

    def test_bundle_does_not_require_visual_capture(self) -> None:
        bundle = ObservationBundle(
            cycle_id="clock-only",
            temporal=TemporalSnapshot(
                observed_at=datetime.now(timezone.utc),
                monotonic_seconds=10.0,
                observer_id="test.clock",
            ),
        )

        self.assertIsNone(bundle.capture)
        self.assertIsNone(bundle.runtime)
        self.assertEqual(bundle.coherence.maximum_skew, timedelta(0))


if __name__ == "__main__":
    unittest.main()
