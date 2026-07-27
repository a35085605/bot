from __future__ import annotations

from datetime import datetime, timedelta, timezone
import unittest

from geometry.rect import Rect
from world_model import (
    CaptureQuality,
    Confidence,
    ControlKey,
    ControlObservation,
    FrameId,
    FrameInfo,
    Presence,
    SceneHypothesis,
    SceneKey,
    SceneObservation,
    WorldSnapshot,
    WorldStateTracker,
)


class WorldModelTest(unittest.TestCase):
    def _snapshot(
        self,
        frame_id: int,
        scene: SceneKey | None,
        *,
        confidence: float = 0.9,
        usable: bool = True,
    ) -> WorldSnapshot:
        hypotheses = (
            ()
            if scene is None
            else (
                SceneHypothesis(
                    scene=scene,
                    confidence=Confidence(confidence),
                ),
            )
        )
        return WorldSnapshot(
            frame=FrameInfo(
                frame_id=FrameId(frame_id),
                captured_at=datetime(
                    2026,
                    7,
                    27,
                    12,
                    0,
                    frame_id,
                    tzinfo=timezone.utc,
                ),
                root_bounds=Rect(
                    x=0,
                    y=0,
                    width=1920,
                    height=1080,
                ),
                source_id="game-window",
            ),
            quality=CaptureQuality(usable=usable),
            scene=SceneObservation(
                resolved=scene,
                hypotheses=hypotheses,
            ),
        )

    def test_semantic_keys_are_normalized(self) -> None:
        self.assertEqual(SceneKey(" battle ").value, "battle")
        self.assertEqual(ControlKey(" confirm ").value, "confirm")

    def test_present_control_requires_root_bounds(self) -> None:
        with self.assertRaises(ValueError):
            ControlObservation(
                control=ControlKey("confirm"),
                presence=Presence.PRESENT,
                confidence=Confidence(0.9),
            )

    def test_non_present_control_rejects_coordinates(self) -> None:
        with self.assertRaises(ValueError):
            ControlObservation(
                control=ControlKey("confirm"),
                presence=Presence.UNKNOWN,
                confidence=Confidence(0.4),
                bounds_root=Rect(
                    x=10,
                    y=20,
                    width=30,
                    height=40,
                ),
            )

    def test_snapshot_owns_immutable_observation_mappings(self) -> None:
        key = ControlKey("confirm")
        observed = {
            key: ControlObservation(
                control=key,
                presence=Presence.PRESENT,
                confidence=Confidence(0.95),
                bounds_root=Rect(
                    x=10,
                    y=20,
                    width=30,
                    height=40,
                ),
                enabled=True,
            )
        }
        snapshot = WorldSnapshot(
            frame=self._snapshot(1, None).frame,
            quality=CaptureQuality(usable=True),
            scene=SceneObservation(),
            controls=observed,
        )

        observed.clear()

        self.assertIsNotNone(snapshot.control(key))
        with self.assertRaises(TypeError):
            snapshot.controls[key] = snapshot.controls[key]

    def test_snapshot_freshness_rejects_future_frames(self) -> None:
        snapshot = self._snapshot(1, SceneKey("battle"))
        captured_at = snapshot.frame.captured_at

        self.assertTrue(
            snapshot.is_fresh(
                captured_at + timedelta(milliseconds=100),
                max_age=timedelta(seconds=1),
            )
        )
        self.assertFalse(
            snapshot.is_fresh(
                captured_at - timedelta(milliseconds=1),
                max_age=timedelta(seconds=1),
            )
        )

    def test_tracker_confirms_scene_across_frames(self) -> None:
        battle = SceneKey("battle")
        tracker = WorldStateTracker(
            scene_confirmation_frames=2,
            minimum_scene_confidence=0.8,
        )

        state1 = tracker.update(self._snapshot(1, battle))
        state2 = tracker.update(self._snapshot(2, battle))

        self.assertIsNone(state1.scene)
        self.assertEqual(state2.scene, battle)
        self.assertTrue(state2.transition_detected)
        self.assertIsNone(state2.previous_scene)

    def test_tracker_preserves_stable_scene_on_unknown_frame(self) -> None:
        battle = SceneKey("battle")
        tracker = WorldStateTracker(scene_confirmation_frames=1)

        tracker.update(self._snapshot(1, battle))
        state = tracker.update(self._snapshot(2, None))

        self.assertEqual(state.scene, battle)
        self.assertFalse(state.transition_detected)

    def test_tracker_reports_semantic_transition(self) -> None:
        battle = SceneKey("battle")
        result = SceneKey("result")
        tracker = WorldStateTracker(scene_confirmation_frames=2)

        tracker.update(self._snapshot(1, battle))
        tracker.update(self._snapshot(2, battle))
        tracker.update(self._snapshot(3, result))
        state = tracker.update(self._snapshot(4, result))

        self.assertEqual(state.scene, result)
        self.assertEqual(state.previous_scene, battle)
        self.assertTrue(state.transition_detected)

    def test_tracker_rejects_out_of_order_frames(self) -> None:
        tracker = WorldStateTracker(scene_confirmation_frames=1)
        tracker.update(self._snapshot(2, SceneKey("battle")))

        with self.assertRaises(ValueError):
            tracker.update(self._snapshot(1, SceneKey("battle")))


if __name__ == "__main__":
    unittest.main()
