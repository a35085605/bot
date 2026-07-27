from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import math
from numbers import Integral, Real
from types import MappingProxyType
from typing import TypeAlias

from geometry.rect import Rect
from world_model.identities import (
    ControlKey,
    IndicatorKey,
    SceneKey,
    ValueKey,
)


ScalarValue: TypeAlias = bool | int | float | str


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


def _normalize_non_empty_text(
    value: object,
    *,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise TypeError(
            f"{field_name} must be a string, "
            f"got {type(value).__name__}"
        )

    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} cannot be empty")

    return normalized


@dataclass(frozen=True, slots=True, order=True)
class FrameId:
    value: int

    def __post_init__(self) -> None:
        if isinstance(self.value, bool) or not isinstance(
            self.value,
            Integral,
        ):
            raise TypeError(
                "frame id must be an integer, "
                f"got {type(self.value).__name__}"
            )

        normalized = int(self.value)
        if normalized < 0:
            raise ValueError("frame id cannot be negative")

        object.__setattr__(self, "value", normalized)


@dataclass(frozen=True, slots=True)
class Confidence:
    value: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_unit_value(
                self.value,
                field_name="confidence",
            ),
        )


class Presence(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class FrameInfo:
    frame_id: FrameId
    captured_at: datetime
    root_bounds: Rect
    source_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.frame_id, FrameId):
            raise TypeError("frame_id must be FrameId")
        if not isinstance(self.captured_at, datetime):
            raise TypeError("captured_at must be datetime")
        if self.captured_at.utcoffset() is None:
            raise ValueError("captured_at must be timezone-aware")
        if not isinstance(self.root_bounds, Rect):
            raise TypeError("root_bounds must be Rect")

        object.__setattr__(
            self,
            "source_id",
            _normalize_non_empty_text(
                self.source_id,
                field_name="frame source id",
            ),
        )


@dataclass(frozen=True, slots=True)
class CaptureQuality:
    usable: bool
    sharpness: float | None = None
    occluded: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.usable, bool):
            raise TypeError("capture usable must be bool")
        if not isinstance(self.occluded, bool):
            raise TypeError("capture occluded must be bool")

        sharpness = self.sharpness
        if sharpness is not None:
            sharpness = _normalize_unit_value(
                sharpness,
                field_name="capture sharpness",
            )
            object.__setattr__(self, "sharpness", sharpness)


@dataclass(frozen=True, slots=True)
class SceneHypothesis:
    scene: SceneKey
    confidence: Confidence

    def __post_init__(self) -> None:
        if not isinstance(self.scene, SceneKey):
            raise TypeError("scene hypothesis scene must be SceneKey")
        if not isinstance(self.confidence, Confidence):
            raise TypeError(
                "scene hypothesis confidence must be Confidence"
            )


@dataclass(frozen=True, slots=True)
class SceneObservation:
    resolved: SceneKey | None = None
    hypotheses: tuple[SceneHypothesis, ...] = field(
        default_factory=tuple
    )

    def __post_init__(self) -> None:
        if self.resolved is not None and not isinstance(
            self.resolved,
            SceneKey,
        ):
            raise TypeError("resolved scene must be SceneKey or None")
        if not isinstance(self.hypotheses, tuple):
            raise TypeError("scene hypotheses must be a tuple")

        seen: set[SceneKey] = set()
        for index, hypothesis in enumerate(self.hypotheses):
            if not isinstance(hypothesis, SceneHypothesis):
                raise TypeError(
                    f"scene hypotheses[{index}] must be "
                    "SceneHypothesis"
                )
            if hypothesis.scene in seen:
                raise ValueError(
                    "scene hypotheses cannot contain duplicate scenes"
                )
            seen.add(hypothesis.scene)

        if self.resolved is not None and self.resolved not in seen:
            raise ValueError(
                "resolved scene must be present in hypotheses"
            )

    @property
    def resolved_confidence(self) -> Confidence | None:
        if self.resolved is None:
            return None

        for hypothesis in self.hypotheses:
            if hypothesis.scene == self.resolved:
                return hypothesis.confidence

        return None

    def confidence_for(
        self,
        scene: SceneKey,
    ) -> Confidence | None:
        if not isinstance(scene, SceneKey):
            raise TypeError("scene must be SceneKey")

        for hypothesis in self.hypotheses:
            if hypothesis.scene == scene:
                return hypothesis.confidence

        return None


@dataclass(frozen=True, slots=True)
class ControlObservation:
    control: ControlKey
    presence: Presence
    confidence: Confidence
    bounds_root: Rect | None = None
    enabled: bool | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.control, ControlKey):
            raise TypeError("control must be ControlKey")
        if not isinstance(self.presence, Presence):
            raise TypeError("control presence must be Presence")
        if not isinstance(self.confidence, Confidence):
            raise TypeError("control confidence must be Confidence")
        if self.bounds_root is not None and not isinstance(
            self.bounds_root,
            Rect,
        ):
            raise TypeError("control bounds_root must be Rect or None")
        if self.enabled is not None and not isinstance(
            self.enabled,
            bool,
        ):
            raise TypeError("control enabled must be bool or None")

        if self.presence is Presence.PRESENT:
            if self.bounds_root is None:
                raise ValueError(
                    "present control must have root bounds"
                )
        else:
            if self.bounds_root is not None:
                raise ValueError(
                    "non-present control cannot have root bounds"
                )
            if self.enabled is not None:
                raise ValueError(
                    "non-present control cannot have enabled state"
                )


@dataclass(frozen=True, slots=True)
class IndicatorObservation:
    indicator: IndicatorKey
    presence: Presence
    confidence: Confidence
    bounds_root: Rect | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.indicator, IndicatorKey):
            raise TypeError("indicator must be IndicatorKey")
        if not isinstance(self.presence, Presence):
            raise TypeError("indicator presence must be Presence")
        if not isinstance(self.confidence, Confidence):
            raise TypeError("indicator confidence must be Confidence")
        if self.bounds_root is not None and not isinstance(
            self.bounds_root,
            Rect,
        ):
            raise TypeError("indicator bounds_root must be Rect or None")

        if self.presence is not Presence.PRESENT:
            if self.bounds_root is not None:
                raise ValueError(
                    "non-present indicator cannot have root bounds"
                )


@dataclass(frozen=True, slots=True)
class ValueObservation:
    value_key: ValueKey
    value: ScalarValue | None
    confidence: Confidence

    def __post_init__(self) -> None:
        if not isinstance(self.value_key, ValueKey):
            raise TypeError("value_key must be ValueKey")
        if not isinstance(self.confidence, Confidence):
            raise TypeError("value confidence must be Confidence")
        if self.value is not None and not isinstance(
            self.value,
            (bool, int, float, str),
        ):
            raise TypeError(
                "observed value must be bool, int, float, str, or None"
            )
        if isinstance(self.value, float) and not math.isfinite(
            self.value
        ):
            raise ValueError("observed float value must be finite")


def _freeze_observation_mapping(
    mapping: Mapping[object, object],
    *,
    key_type: type,
    value_type: type,
    identity_attribute: str,
    field_name: str,
) -> Mapping[object, object]:
    if not isinstance(mapping, Mapping):
        raise TypeError(f"{field_name} must be a mapping")

    copied: dict[object, object] = {}
    for key, observation in mapping.items():
        if not isinstance(key, key_type):
            raise TypeError(
                f"{field_name} key must be {key_type.__name__}"
            )
        if not isinstance(observation, value_type):
            raise TypeError(
                f"{field_name}[{key!r}] must be "
                f"{value_type.__name__}"
            )
        if getattr(observation, identity_attribute) != key:
            raise ValueError(
                f"{field_name} key must equal observation identity"
            )
        copied[key] = observation

    return MappingProxyType(copied)


@dataclass(frozen=True, slots=True)
class WorldSnapshot:
    frame: FrameInfo
    quality: CaptureQuality
    scene: SceneObservation
    controls: Mapping[ControlKey, ControlObservation] = field(
        default_factory=dict
    )
    indicators: Mapping[IndicatorKey, IndicatorObservation] = field(
        default_factory=dict
    )
    values: Mapping[ValueKey, ValueObservation] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(self.frame, FrameInfo):
            raise TypeError("snapshot frame must be FrameInfo")
        if not isinstance(self.quality, CaptureQuality):
            raise TypeError(
                "snapshot quality must be CaptureQuality"
            )
        if not isinstance(self.scene, SceneObservation):
            raise TypeError(
                "snapshot scene must be SceneObservation"
            )

        object.__setattr__(
            self,
            "controls",
            _freeze_observation_mapping(
                self.controls,
                key_type=ControlKey,
                value_type=ControlObservation,
                identity_attribute="control",
                field_name="snapshot controls",
            ),
        )
        object.__setattr__(
            self,
            "indicators",
            _freeze_observation_mapping(
                self.indicators,
                key_type=IndicatorKey,
                value_type=IndicatorObservation,
                identity_attribute="indicator",
                field_name="snapshot indicators",
            ),
        )
        object.__setattr__(
            self,
            "values",
            _freeze_observation_mapping(
                self.values,
                key_type=ValueKey,
                value_type=ValueObservation,
                identity_attribute="value_key",
                field_name="snapshot values",
            ),
        )

    def control(
        self,
        key: ControlKey,
    ) -> ControlObservation | None:
        return self.controls.get(key)

    def indicator(
        self,
        key: IndicatorKey,
    ) -> IndicatorObservation | None:
        return self.indicators.get(key)

    def observed_value(
        self,
        key: ValueKey,
    ) -> ValueObservation | None:
        return self.values.get(key)

    def age(self, now: datetime) -> timedelta:
        if not isinstance(now, datetime):
            raise TypeError("now must be datetime")
        if now.utcoffset() is None:
            raise ValueError("now must be timezone-aware")
        return now - self.frame.captured_at

    def is_fresh(
        self,
        now: datetime,
        *,
        max_age: timedelta,
    ) -> bool:
        if not isinstance(max_age, timedelta):
            raise TypeError("max_age must be timedelta")
        if max_age < timedelta(0):
            raise ValueError("max_age cannot be negative")

        age = self.age(now)
        return timedelta(0) <= age <= max_age
