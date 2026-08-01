from __future__ import annotations

from datetime import datetime, timezone
import unittest

from content import ContentFrame, ContentPlacementInCapture
from evidence import EvidenceSet
from geometry.rect import Rect
from observation.capture import (
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

    def test_world_snapshot_uses_content_frame(self) -> None:
        content = self._content()
        evidence_set = EvidenceSet(
            frame_id=content.frame.frame_id,
            source_id=content.frame.source_id,
            root_bounds=content.bounds_content,
        )

        snapshot = SemanticSnapshotBuilder(
            SemanticPerceptionConfig()
        ).build(
            content=content,
            quality=CaptureQuality(usable=True),
            evidence_set=evidence_set,
        )

        self.assertEqual(
            snapshot.frame.root_bounds,
            Rect(x=0, y=0, width=1600, height=900),
        )
        self.assertNotEqual(
            snapshot.frame.root_bounds,
            content.capture.root_bounds,
        )

    def test_builder_rejects_raw_capture_bounds_for_cropped_content(self) -> None:
        content = self._content()

        with self.assertRaises(ValueError):
            SemanticSnapshotBuilder(
                SemanticPerceptionConfig()
            ).build(
                content=content,
                quality=CaptureQuality(usable=True),
                evidence_set=EvidenceSet(
                    frame_id=content.frame.frame_id,
                    source_id=content.frame.source_id,
                    root_bounds=content.capture.root_bounds,
                ),
            )

    def test_builder_requires_one_context_input(self) -> None:
        content = self._content()
        evidence_set = EvidenceSet(
            frame_id=content.frame.frame_id,
            source_id=content.frame.source_id,
            root_bounds=content.bounds_content,
        )
        builder = SemanticSnapshotBuilder(SemanticPerceptionConfig())

        with self.assertRaises(ValueError):
            builder.build(
                content=content,
                frame=content.capture,
                quality=CaptureQuality(usable=True),
                evidence_set=evidence_set,
            )


if __name__ == "__main__":
    unittest.main()
