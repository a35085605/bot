from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from numbers import Integral

from observation.capture import FrameId
from world_model.identities import (
    ControlKey,
    IndicatorKey,
    SceneKey,
    ValueKey,
)
from world_model.models import (
    Confidence,
    ControlObservation,
    IndicatorObservation,
    ValueObservation,
    WorldSnapshot,
)


@dataclass(frozen=True, slots=True)
class StableScene:
    scene: SceneKey
    confidence: Confidence
    since_frame: FrameId

    def __post_init__(self) -> None:
        if not isinstance(self.scene, SceneKey):
            raise TypeError("stable scene must be SceneKey")
        if not isinstance(self.confidence, Confidence):
            raise TypeError(
                "stable scene confidence must be Confidence"
            )
        if not isinstance(self.since_frame, FrameId):
            raise TypeError("stable scene since_frame must be FrameId")


@dataclass(frozen=True, slots=True)
class WorldState:
    revision: int
    latest_snapshot: WorldSnapshot
    stable_scene: StableScene | None
    previous_scene: SceneKey | None
    transition_detected: bool

    def __post_init__(self) -> None:
        if isinstance(self.revision, bool) or not isinstance(
            self.revision,
            Integral,
        ):
            raise TypeError("world state revision must be an integer")
        if self.revision <= 0:
            raise ValueError(
                "world state revision must be greater than zero"
            )
        if not isinstance(self.latest_snapshot, WorldSnapshot):
            raise TypeError(
                "latest_snapshot must be WorldSnapshot"
            )
        if self.stable_scene is not None and not isinstance(
            self.stable_scene,
            StableScene,
        ):
            raise TypeError(
                "stable_scene must be StableScene or None"
            )
        if self.previous_scene is not None and not isinstance(
            self.previous_scene,
            SceneKey,
        ):
            raise TypeError(
                "previous_scene must be SceneKey or None"
            )
        if not isinstance(self.transition_detected, bool):
            raise TypeError("transition_detected must be bool")

        object.__setattr__(self, "revision", int(self.revision))

    @property
    def scene(self) -> SceneKey | None:
        if self.stable_scene is None:
            return None
        return self.stable_scene.scene

    @property
    def controls(
        self,
    ) -> Mapping[ControlKey, ControlObservation]:
        return self.latest_snapshot.controls

    @property
    def indicators(
        self,
    ) -> Mapping[IndicatorKey, IndicatorObservation]:
        return self.latest_snapshot.indicators

    @property
    def values(
        self,
    ) -> Mapping[ValueKey, ValueObservation]:
        return self.latest_snapshot.values

    def control(
        self,
        key: ControlKey,
    ) -> ControlObservation | None:
        return self.latest_snapshot.control(key)

    def indicator(
        self,
        key: IndicatorKey,
    ) -> IndicatorObservation | None:
        return self.latest_snapshot.indicator(key)

    def observed_value(
        self,
        key: ValueKey,
    ) -> ValueObservation | None:
        return self.latest_snapshot.observed_value(key)

    def age(self, now: datetime) -> timedelta:
        return self.latest_snapshot.age(now)

    def is_fresh(
        self,
        now: datetime,
        *,
        max_age: timedelta,
    ) -> bool:
        return self.latest_snapshot.is_fresh(
            now,
            max_age=max_age,
        )


class WorldStateTracker:
    """Stabilize semantic scene observations across ordered frames."""

    def __init__(
        self,
        *,
        scene_confirmation_frames: int = 3,
        minimum_scene_confidence: float = 0.0,
    ) -> None:
        if (
            isinstance(scene_confirmation_frames, bool)
            or not isinstance(scene_confirmation_frames, Integral)
        ):
            raise TypeError(
                "scene_confirmation_frames must be an integer"
            )

        normalized_confirmation_frames = int(
            scene_confirmation_frames
        )
        if normalized_confirmation_frames <= 0:
            raise ValueError(
                "scene_confirmation_frames must be greater than zero"
            )

        self._scene_confirmation_frames = (
            normalized_confirmation_frames
        )
        self._minimum_scene_confidence = Confidence(
            minimum_scene_confidence
        )
        self._state: WorldState | None = None
        self._pending_scene: SceneKey | None = None
        self._pending_count = 0

    @property
    def state(self) -> WorldState | None:
        return self._state

    def update(self, snapshot: WorldSnapshot) -> WorldState:
        if not isinstance(snapshot, WorldSnapshot):
            raise TypeError("snapshot must be WorldSnapshot")

        self._validate_frame_order(snapshot)

        candidate = self._scene_candidate(snapshot)
        previous_stable = (
            None
            if self._state is None
            else self._state.stable_scene
        )
        stable_scene = previous_stable
        previous_scene = (
            None
            if previous_stable is None
            else previous_stable.scene
        )
        transition_detected = False

        if candidate is None:
            self._reset_pending()
        elif (
            previous_stable is not None
            and candidate.scene == previous_stable.scene
        ):
            stable_scene = StableScene(
                scene=candidate.scene,
                confidence=candidate.confidence,
                since_frame=previous_stable.since_frame,
            )
            self._reset_pending()
        else:
            if candidate.scene == self._pending_scene:
                self._pending_count += 1
            else:
                self._pending_scene = candidate.scene
                self._pending_count = 1

            if (
                self._pending_count
                >= self._scene_confirmation_frames
            ):
                stable_scene = StableScene(
                    scene=candidate.scene,
                    confidence=candidate.confidence,
                    since_frame=snapshot.frame.frame_id,
                )
                transition_detected = (
                    previous_scene != candidate.scene
                )
                self._reset_pending()

        revision = 1 if self._state is None else self._state.revision + 1
        state = WorldState(
            revision=revision,
            latest_snapshot=snapshot,
            stable_scene=stable_scene,
            previous_scene=(
                previous_scene
                if transition_detected
                else (
                    None
                    if self._state is None
                    else self._state.previous_scene
                )
            ),
            transition_detected=transition_detected,
        )
        self._state = state
        return state

    def _scene_candidate(
        self,
        snapshot: WorldSnapshot,
    ) -> StableScene | None:
        if not snapshot.quality.usable:
            return None

        scene = snapshot.scene.resolved
        confidence = snapshot.scene.resolved_confidence
        if scene is None or confidence is None:
            return None
        if confidence.value < self._minimum_scene_confidence.value:
            return None

        return StableScene(
            scene=scene,
            confidence=confidence,
            since_frame=snapshot.frame.frame_id,
        )

    def _validate_frame_order(
        self,
        snapshot: WorldSnapshot,
    ) -> None:
        if self._state is None:
            return

        previous = self._state.latest_snapshot.frame
        current = snapshot.frame

        if current.source_id != previous.source_id:
            raise ValueError(
                "world state tracker cannot mix frame sources"
            )
        if current.stream_id != previous.stream_id:
            raise ValueError(
                "world state tracker cannot mix capture streams"
            )
        if current.frame_id.value <= previous.frame_id.value:
            raise ValueError(
                "world state tracker requires increasing frame ids"
            )
        if current.captured_at < previous.captured_at:
            raise ValueError(
                "world state tracker requires non-decreasing capture times"
            )

    def _reset_pending(self) -> None:
        self._pending_scene = None
        self._pending_count = 0
