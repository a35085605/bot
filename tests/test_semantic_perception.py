from __future__ import annotations

from datetime import datetime, timezone
import unittest

from evidence import (
    Evidence,
    EvidenceId,
    EvidenceKind,
    EvidenceProvenance,
    EvidenceSet,
)
from geometry.rect import Rect
from observation.capture import (
    CaptureQuality,
    CaptureStreamId,
    CaptureSurface,
    CoordinateSpace,
    CoordinateTransform,
    FrameId,
    FrameInfo,
)
from semantic_perception import (
    ControlRule,
    EvidenceRequirement,
    SceneRule,
    SemanticPerceptionConfig,
    SemanticSnapshotBuilder,
)
from world_model import (
    ControlKey,
    Presence,
    SceneKey,
    WorldStateTracker,
)


class SemanticPerceptionTest(unittest.TestCase):
    def _frame(self, frame_id: int) -> FrameInfo:
        return FrameInfo(
            frame_id=FrameId(frame_id),
            stream_id=CaptureStreamId("capture-session-1"),
            captured_at=datetime(
                2026,
                7,
                28,
                3,
                0,
                frame_id,
                tzinfo=timezone.utc,
            ),
            root_bounds=Rect(x=0, y=0, width=1920, height=1080),
            source_id="game-window",
            surface=CaptureSurface(
                surface_id="hwnd:42",
                client_bounds_screen=Rect(
                    x=100,
                    y=200,
                    width=1920,
                    height=1080,
                ),
            ),
            root_to_screen=CoordinateTransform(
                source=CoordinateSpace.ROOT,
                target=CoordinateSpace.SCREEN,
                offset_x=100,
                offset_y=200,
            ),
            capture_backend_id="test.capture",
        )

    def _evidence(
        self,
        frame_id: int,
        evidence_id: str,
        asset_key: str,
        *,
        score: float,
        bounds_root: Rect | None = None,
    ) -> Evidence[object]:
        return Evidence(
            evidence_id=EvidenceId(evidence_id),
            frame_id=FrameId(frame_id),
            source_id="game-window",
            kind=EvidenceKind("template.match"),
            score=score,
            roi_root=Rect(x=0, y=0, width=1920, height=1080),
            bounds_root=bounds_root,
            provenance=EvidenceProvenance(
                detector_id="opencv.template",
                asset_keys=(asset_key,),
            ),
            result={"template_key": asset_key},
        )

    def _evidence_set(
        self,
        frame_id: int,
        *items: Evidence[object],
    ) -> EvidenceSet:
        return EvidenceSet(
            frame_id=FrameId(frame_id),
            source_id="game-window",
            root_bounds=Rect(x=0, y=0, width=1920, height=1080),
            items=items,
        )

    def _builder(self) -> SemanticSnapshotBuilder:
        template_match = EvidenceKind("template.match")
        return SemanticSnapshotBuilder(
            SemanticPerceptionConfig(
                scene_rules=(
                    SceneRule(
                        scene=SceneKey("login"),
                        requirements=(
                            EvidenceRequirement(
                                kind=template_match,
                                minimum_score=0.8,
                                asset_key="scene.login",
                            ),
                        ),
                    ),
                    SceneRule(
                        scene=SceneKey("lobby"),
                        requirements=(
                            EvidenceRequirement(
                                kind=template_match,
                                minimum_score=0.8,
                                asset_key="scene.lobby",
                            ),
                        ),
                    ),
                ),
                control_rules=(
                    ControlRule(
                        control=ControlKey("submit"),
                        requirement=EvidenceRequirement(
                            kind=template_match,
                            minimum_score=0.8,
                            asset_key="ui.submit",
                        ),
                        enabled=True,
                    ),
                ),
                minimum_resolved_scene_confidence=0.85,
                scene_resolution_margin=0.05,
            )
        )

    def test_builds_resolved_scene_and_localized_control(self) -> None:
        frame = self._frame(1)
        submit_bounds = Rect(x=800, y=700, width=180, height=60)
        evidence_set = self._evidence_set(
            1,
            self._evidence(
                1,
                "scene-login",
                "scene.login",
                score=0.94,
            ),
            self._evidence(
                1,
                "submit",
                "ui.submit",
                score=0.91,
                bounds_root=submit_bounds,
            ),
        )

        snapshot = self._builder().build(
            frame=frame,
            quality=CaptureQuality(usable=True),
            evidence_set=evidence_set,
        )

        self.assertEqual(snapshot.scene.resolved, SceneKey("login"))
        control = snapshot.control(ControlKey("submit"))
        self.assertIsNotNone(control)
        assert control is not None
        self.assertEqual(control.presence, Presence.PRESENT)
        self.assertEqual(control.bounds_root, submit_bounds)
        self.assertTrue(control.enabled)

    def test_keeps_scene_unresolved_when_hypotheses_are_too_close(
        self,
    ) -> None:
        frame = self._frame(1)
        snapshot = self._builder().build(
            frame=frame,
            quality=CaptureQuality(usable=True),
            evidence_set=self._evidence_set(
                1,
                self._evidence(
                    1,
                    "scene-login",
                    "scene.login",
                    score=0.91,
                ),
                self._evidence(
                    1,
                    "scene-lobby",
                    "scene.lobby",
                    score=0.89,
                ),
            ),
        )

        self.assertIsNone(snapshot.scene.resolved)
        self.assertEqual(
            tuple(item.scene.value for item in snapshot.scene.hypotheses),
            ("login", "lobby"),
        )

    def test_missing_localized_evidence_produces_unknown_control(self) -> None:
        snapshot = self._builder().build(
            frame=self._frame(1),
            quality=CaptureQuality(usable=True),
            evidence_set=self._evidence_set(
                1,
                self._evidence(
                    1,
                    "submit-non-localized",
                    "ui.submit",
                    score=0.95,
                ),
            ),
        )

        control = snapshot.control(ControlKey("submit"))
        self.assertIsNotNone(control)
        assert control is not None
        self.assertEqual(control.presence, Presence.UNKNOWN)
        self.assertEqual(control.confidence.value, 0.0)

    def test_unusable_frame_suppresses_semantic_observations(self) -> None:
        snapshot = self._builder().build(
            frame=self._frame(1),
            quality=CaptureQuality(usable=False),
            evidence_set=self._evidence_set(
                1,
                self._evidence(
                    1,
                    "scene-login",
                    "scene.login",
                    score=0.99,
                ),
                self._evidence(
                    1,
                    "submit",
                    "ui.submit",
                    score=0.99,
                    bounds_root=Rect(
                        x=800,
                        y=700,
                        width=180,
                        height=60,
                    ),
                ),
            ),
        )

        self.assertIsNone(snapshot.scene.resolved)
        self.assertFalse(snapshot.scene.hypotheses)
        control = snapshot.control(ControlKey("submit"))
        self.assertIsNotNone(control)
        assert control is not None
        self.assertEqual(control.presence, Presence.UNKNOWN)

    def test_rejects_evidence_from_a_different_frame(self) -> None:
        with self.assertRaises(ValueError):
            self._builder().build(
                frame=self._frame(2),
                quality=CaptureQuality(usable=True),
                evidence_set=self._evidence_set(1),
            )

    def test_snapshot_builder_feeds_world_state_tracker(self) -> None:
        builder = self._builder()
        tracker = WorldStateTracker(
            scene_confirmation_frames=2,
            minimum_scene_confidence=0.85,
        )

        first = builder.build(
            frame=self._frame(1),
            quality=CaptureQuality(usable=True),
            evidence_set=self._evidence_set(
                1,
                self._evidence(
                    1,
                    "scene-login-1",
                    "scene.login",
                    score=0.93,
                ),
            ),
        )
        second = builder.build(
            frame=self._frame(2),
            quality=CaptureQuality(usable=True),
            evidence_set=self._evidence_set(
                2,
                self._evidence(
                    2,
                    "scene-login-2",
                    "scene.login",
                    score=0.92,
                ),
            ),
        )

        self.assertIsNone(tracker.update(first).scene)
        self.assertEqual(tracker.update(second).scene, SceneKey("login"))


if __name__ == "__main__":
    unittest.main()
