from __future__ import annotations

from datetime import datetime, timezone
import unittest

from evidence import EvidenceSet
from geometry.point import Point
from geometry.rect import Rect
from observation import (
    CaptureQuality,
    CaptureStreamId,
    CoordinateSpace,
    CoordinateTransform,
    FrameId,
    FrameInfo,
)
from semantic_perception import (
    SemanticPerceptionConfig,
    SemanticSnapshotBuilder,
)
from viewport import CanonicalViewport, ViewportPlacement


class CanonicalViewportFlowTest(unittest.TestCase):
    def _observation(self) -> FrameInfo:
        return FrameInfo(
            frame_id=FrameId(3),
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
            source_id="desktop-capture",
            window=None,
            root_to_screen=CoordinateTransform(
                source=CoordinateSpace.ROOT,
                target=CoordinateSpace.SCREEN,
                offset_x=100,
                offset_y=200,
            ),
            capture_backend="test.capture",
        )

    def _viewport(self) -> CanonicalViewport:
        return CanonicalViewport(
            observation=self._observation(),
            placement=ViewportPlacement(
                source_bounds_capture=Rect(
                    x=160,
                    y=120,
                    width=1600,
                    height=900,
                ),
            ),
        )

    def test_world_snapshot_uses_canonical_viewport_frame(self) -> None:
        viewport = self._viewport()
        evidence_set = EvidenceSet(
            frame_id=viewport.frame.frame_id,
            source_id=viewport.frame.source_id,
            root_bounds=viewport.root_bounds,
        )

        snapshot = SemanticSnapshotBuilder(
            SemanticPerceptionConfig()
        ).build(
            viewport=viewport,
            quality=CaptureQuality(usable=True),
            evidence_set=evidence_set,
        )

        self.assertEqual(
            snapshot.frame.root_bounds,
            Rect(x=0, y=0, width=1600, height=900),
        )
        self.assertNotEqual(
            snapshot.frame.root_bounds,
            viewport.observation.root_bounds,
        )
        self.assertEqual(
            snapshot.frame.root_point_to_screen(Point(x=10, y=20)),
            Point(x=270, y=340),
        )

    def test_builder_rejects_raw_capture_bounds_for_cropped_viewport(self) -> None:
        viewport = self._viewport()

        with self.assertRaises(ValueError):
            SemanticSnapshotBuilder(
                SemanticPerceptionConfig()
            ).build(
                viewport=viewport,
                quality=CaptureQuality(usable=True),
                evidence_set=EvidenceSet(
                    frame_id=viewport.frame.frame_id,
                    source_id=viewport.frame.source_id,
                    root_bounds=viewport.observation.root_bounds,
                ),
            )

    def test_builder_requires_one_context_input(self) -> None:
        viewport = self._viewport()
        evidence_set = EvidenceSet(
            frame_id=viewport.frame.frame_id,
            source_id=viewport.frame.source_id,
            root_bounds=viewport.root_bounds,
        )
        builder = SemanticSnapshotBuilder(SemanticPerceptionConfig())

        with self.assertRaises(ValueError):
            builder.build(
                viewport=viewport,
                frame=viewport.frame,
                quality=CaptureQuality(usable=True),
                evidence_set=evidence_set,
            )


if __name__ == "__main__":
    unittest.main()
