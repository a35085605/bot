from __future__ import annotations

from evidence import Evidence, EvidenceSet
from observation import CaptureQuality, FrameInfo
from semantic_perception.rules import (
    ControlRule,
    EvidenceRequirement,
    SceneRule,
    SemanticPerceptionConfig,
)
from viewport import CanonicalViewport, ViewportPlacement
from world_model import (
    Confidence,
    ControlKey,
    ControlObservation,
    Presence,
    SceneHypothesis,
    SceneObservation,
    WorldSnapshot,
)


class SemanticSnapshotBuilder:
    """Build one semantic world snapshot from canonical viewport evidence."""

    def __init__(self, config: SemanticPerceptionConfig) -> None:
        if not isinstance(config, SemanticPerceptionConfig):
            raise TypeError("config must be SemanticPerceptionConfig")
        self._config = config

    def build(
        self,
        *,
        quality: CaptureQuality,
        evidence_set: EvidenceSet,
        viewport: CanonicalViewport | None = None,
        frame: FrameInfo | None = None,
    ) -> WorldSnapshot:
        """
        Build from a canonical viewport.

        ``frame`` remains as a compatibility path for callers whose capture is
        already the canonical viewport. New orchestration should pass
        ``viewport`` explicitly so cropped or normalized coordinate spaces
        cannot be confused with raw capture-root.
        """

        if (viewport is None) == (frame is None):
            raise ValueError("provide exactly one of viewport or frame")
        if viewport is not None and not isinstance(
            viewport,
            CanonicalViewport,
        ):
            raise TypeError("viewport must be CanonicalViewport or None")
        if frame is not None and not isinstance(frame, FrameInfo):
            raise TypeError("frame must be FrameInfo or None")
        if not isinstance(quality, CaptureQuality):
            raise TypeError("quality must be CaptureQuality")
        if not isinstance(evidence_set, EvidenceSet):
            raise TypeError("evidence_set must be EvidenceSet")

        if viewport is None:
            assert frame is not None
            viewport = CanonicalViewport(
                observation=frame,
                placement=ViewportPlacement(
                    source_bounds_capture=frame.root_bounds,
                ),
            )

        self._validate_context(viewport, evidence_set)

        if quality.usable:
            scene = self._build_scene(evidence_set)
            controls = self._build_controls(evidence_set)
        else:
            scene = SceneObservation()
            controls = self._unknown_controls()

        return WorldSnapshot(
            frame=viewport.frame,
            quality=quality,
            scene=scene,
            controls=controls,
        )

    @staticmethod
    def _validate_context(
        viewport: CanonicalViewport,
        evidence_set: EvidenceSet,
    ) -> None:
        frame = viewport.frame
        if evidence_set.frame_id != frame.frame_id:
            raise ValueError(
                "evidence set frame_id must match viewport frame_id"
            )
        if evidence_set.source_id != frame.source_id:
            raise ValueError(
                "evidence set source_id must match viewport source_id"
            )
        if evidence_set.root_bounds != viewport.root_bounds:
            raise ValueError(
                "evidence set root_bounds must match canonical viewport bounds"
            )

    def _build_scene(self, evidence_set: EvidenceSet) -> SceneObservation:
        hypotheses = tuple(
            sorted(
                (
                    hypothesis
                    for rule in self._config.scene_rules
                    if (
                        hypothesis := self._scene_hypothesis(
                            rule,
                            evidence_set,
                        )
                    )
                    is not None
                ),
                key=lambda hypothesis: (
                    -hypothesis.confidence.value,
                    hypothesis.scene.value,
                ),
            )
        )

        resolved = None
        if hypotheses:
            best = hypotheses[0]
            runner_up = (
                None if len(hypotheses) == 1 else hypotheses[1]
            )
            has_confidence = (
                best.confidence.value
                >= self._config.minimum_resolved_scene_confidence
            )
            has_margin = (
                runner_up is None
                or best.confidence.value - runner_up.confidence.value
                >= self._config.scene_resolution_margin
            )
            if has_confidence and has_margin:
                resolved = best.scene

        return SceneObservation(
            resolved=resolved,
            hypotheses=hypotheses,
        )

    @staticmethod
    def _scene_hypothesis(
        rule: SceneRule,
        evidence_set: EvidenceSet,
    ) -> SceneHypothesis | None:
        matched_scores: list[float] = []
        for requirement in rule.requirements:
            evidence = SemanticSnapshotBuilder._best_evidence(
                evidence_set,
                requirement,
            )
            if evidence is None:
                return None
            matched_scores.append(evidence.score)

        return SceneHypothesis(
            scene=rule.scene,
            confidence=Confidence(min(matched_scores)),
        )

    def _build_controls(
        self,
        evidence_set: EvidenceSet,
    ) -> dict[ControlKey, ControlObservation]:
        return {
            rule.control: self._control_observation(rule, evidence_set)
            for rule in self._config.control_rules
        }

    def _unknown_controls(
        self,
    ) -> dict[ControlKey, ControlObservation]:
        return {
            rule.control: ControlObservation(
                control=rule.control,
                presence=Presence.UNKNOWN,
                confidence=Confidence(0.0),
            )
            for rule in self._config.control_rules
        }

    @staticmethod
    def _control_observation(
        rule: ControlRule,
        evidence_set: EvidenceSet,
    ) -> ControlObservation:
        evidence = SemanticSnapshotBuilder._best_evidence(
            evidence_set,
            rule.requirement,
            require_bounds=True,
        )
        if evidence is None:
            return ControlObservation(
                control=rule.control,
                presence=Presence.UNKNOWN,
                confidence=Confidence(0.0),
            )

        return ControlObservation(
            control=rule.control,
            presence=Presence.PRESENT,
            confidence=Confidence(evidence.score),
            bounds_root=evidence.bounds_root,
            enabled=rule.enabled,
        )

    @staticmethod
    def _best_evidence(
        evidence_set: EvidenceSet,
        requirement: EvidenceRequirement,
        *,
        require_bounds: bool = False,
    ) -> Evidence[object] | None:
        candidates = (
            evidence
            for evidence in evidence_set
            if requirement.matches(evidence)
            and (not require_bounds or evidence.bounds_root is not None)
        )
        return max(
            candidates,
            key=lambda evidence: (
                evidence.score,
                evidence.evidence_id.value,
            ),
            default=None,
        )
