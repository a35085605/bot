from __future__ import annotations

from dataclasses import dataclass, field
import math
from numbers import Real

from evidence import Evidence, EvidenceKind
from world_model import ControlKey, SceneKey


def _normalize_optional_text(
    value: object,
    *,
    field_name: str,
) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(
            f"{field_name} must be a string or None, "
            f"got {type(value).__name__}"
        )

    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} cannot be empty")
    return normalized


def _normalize_unit_value(
    value: object,
    *,
    field_name: str,
) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(
            f"{field_name} must be a real number, "
            f"got {type(value).__name__}"
        )

    normalized = float(value)
    if not math.isfinite(normalized):
        raise ValueError(f"{field_name} must be finite")
    if not 0.0 <= normalized <= 1.0:
        raise ValueError(
            f"{field_name} must be between 0 and 1, "
            f"got {normalized}"
        )
    return normalized


@dataclass(frozen=True, slots=True)
class EvidenceRequirement:
    """Select evidence using stable detector-independent metadata."""

    kind: EvidenceKind
    minimum_score: float = 0.0
    detector_id: str | None = None
    asset_key: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, EvidenceKind):
            raise TypeError("evidence requirement kind must be EvidenceKind")

        object.__setattr__(
            self,
            "minimum_score",
            _normalize_unit_value(
                self.minimum_score,
                field_name="evidence requirement minimum_score",
            ),
        )
        object.__setattr__(
            self,
            "detector_id",
            _normalize_optional_text(
                self.detector_id,
                field_name="evidence requirement detector_id",
            ),
        )
        object.__setattr__(
            self,
            "asset_key",
            _normalize_optional_text(
                self.asset_key,
                field_name="evidence requirement asset_key",
            ),
        )

    def matches(self, evidence: Evidence[object]) -> bool:
        if not isinstance(evidence, Evidence):
            raise TypeError("evidence must be Evidence")
        if evidence.kind != self.kind:
            return False
        if evidence.score < self.minimum_score:
            return False
        if (
            self.detector_id is not None
            and evidence.provenance.detector_id != self.detector_id
        ):
            return False
        if (
            self.asset_key is not None
            and self.asset_key not in evidence.provenance.asset_keys
        ):
            return False
        return True


@dataclass(frozen=True, slots=True)
class SceneRule:
    """Resolve one semantic scene from one or more evidence requirements."""

    scene: SceneKey
    requirements: tuple[EvidenceRequirement, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.scene, SceneKey):
            raise TypeError("scene rule scene must be SceneKey")
        if not isinstance(self.requirements, tuple):
            raise TypeError("scene rule requirements must be a tuple")
        if not self.requirements:
            raise ValueError("scene rule requires at least one requirement")

        for index, requirement in enumerate(self.requirements):
            if not isinstance(requirement, EvidenceRequirement):
                raise TypeError(
                    f"scene rule requirements[{index}] must be "
                    "EvidenceRequirement"
                )

        if len(set(self.requirements)) != len(self.requirements):
            raise ValueError(
                "scene rule cannot contain duplicate requirements"
            )


@dataclass(frozen=True, slots=True)
class ControlRule:
    """Map localized evidence to one semantic control observation."""

    control: ControlKey
    requirement: EvidenceRequirement
    enabled: bool | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.control, ControlKey):
            raise TypeError("control rule control must be ControlKey")
        if not isinstance(self.requirement, EvidenceRequirement):
            raise TypeError(
                "control rule requirement must be EvidenceRequirement"
            )
        if self.enabled is not None and not isinstance(self.enabled, bool):
            raise TypeError("control rule enabled must be bool or None")


@dataclass(frozen=True, slots=True)
class SemanticPerceptionConfig:
    """Declarative configuration for evidence-to-world interpretation."""

    scene_rules: tuple[SceneRule, ...] = field(default_factory=tuple)
    control_rules: tuple[ControlRule, ...] = field(default_factory=tuple)
    minimum_resolved_scene_confidence: float = 0.8
    scene_resolution_margin: float = 0.05

    def __post_init__(self) -> None:
        if not isinstance(self.scene_rules, tuple):
            raise TypeError("scene_rules must be a tuple")
        if not isinstance(self.control_rules, tuple):
            raise TypeError("control_rules must be a tuple")

        seen_scenes: set[SceneKey] = set()
        for index, rule in enumerate(self.scene_rules):
            if not isinstance(rule, SceneRule):
                raise TypeError(
                    f"scene_rules[{index}] must be SceneRule"
                )
            if rule.scene in seen_scenes:
                raise ValueError(
                    "scene_rules cannot contain duplicate scenes"
                )
            seen_scenes.add(rule.scene)

        seen_controls: set[ControlKey] = set()
        for index, rule in enumerate(self.control_rules):
            if not isinstance(rule, ControlRule):
                raise TypeError(
                    f"control_rules[{index}] must be ControlRule"
                )
            if rule.control in seen_controls:
                raise ValueError(
                    "control_rules cannot contain duplicate controls"
                )
            seen_controls.add(rule.control)

        object.__setattr__(
            self,
            "minimum_resolved_scene_confidence",
            _normalize_unit_value(
                self.minimum_resolved_scene_confidence,
                field_name="minimum resolved scene confidence",
            ),
        )
        object.__setattr__(
            self,
            "scene_resolution_margin",
            _normalize_unit_value(
                self.scene_resolution_margin,
                field_name="scene resolution margin",
            ),
        )
