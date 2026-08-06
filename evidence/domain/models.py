from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
import math
from numbers import Real
from typing import Generic, TypeVar

from geometry.rect import Rect
from observation.capture import FrameId


ResultT = TypeVar("ResultT", covariant=True)


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


def _normalize_optional_text(
    value: object,
    *,
    field_name: str,
) -> str | None:
    if value is None:
        return None
    return _normalize_non_empty_text(
        value,
        field_name=field_name,
    )


def _normalize_unit_score(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(
            "evidence score must be a real number, "
            f"got {type(value).__name__}"
        )

    normalized = float(value)
    if not math.isfinite(normalized):
        raise ValueError("evidence score must be finite")
    if not 0.0 <= normalized <= 1.0:
        raise ValueError(
            "evidence score must be between 0 and 1, "
            f"got {normalized}"
        )

    return normalized


def _normalize_string_tuple(
    values: object,
    *,
    field_name: str,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes, bytearray)):
        raise TypeError(
            f"{field_name} must be an iterable of strings, "
            "not a single string"
        )

    try:
        items = tuple(values)  # type: ignore[arg-type]
    except TypeError as exc:
        raise TypeError(
            f"{field_name} must be iterable"
        ) from exc

    normalized = tuple(
        _normalize_non_empty_text(
            item,
            field_name=f"{field_name}[{index}]",
        )
        for index, item in enumerate(items)
    )

    if len(set(normalized)) != len(normalized):
        raise ValueError(
            f"{field_name} cannot contain duplicate values"
        )

    return normalized


@dataclass(frozen=True, slots=True, order=True)
class EvidenceId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_non_empty_text(
                self.value,
                field_name="evidence id",
            ),
        )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True, order=True)
class EvidenceKind:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_non_empty_text(
                self.value,
                field_name="evidence kind",
            ),
        )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class EvidenceProvenance:
    """Runtime provenance describing how one evidence item was produced."""

    detector_id: str
    detector_version: str | None = None
    parameter_digest: str | None = None
    asset_keys: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "detector_id",
            _normalize_non_empty_text(
                self.detector_id,
                field_name="evidence detector id",
            ),
        )
        object.__setattr__(
            self,
            "detector_version",
            _normalize_optional_text(
                self.detector_version,
                field_name="evidence detector version",
            ),
        )
        object.__setattr__(
            self,
            "parameter_digest",
            _normalize_optional_text(
                self.parameter_digest,
                field_name="evidence parameter digest",
            ),
        )
        object.__setattr__(
            self,
            "asset_keys",
            _normalize_string_tuple(
                self.asset_keys,
                field_name="evidence asset keys",
            ),
        )


@dataclass(frozen=True, slots=True)
class Evidence(Generic[ResultT]):
    """
    Immutable detector output for one frame and one searched region.

    ``score`` is normalized to ``[0, 1]`` and larger values always mean
    stronger evidence. ``roi_root`` and ``bounds_root`` use root-coordinate
    half-open rectangles. A detector-specific immutable result is carried in
    ``result`` without coupling this package to template, OCR, colour, hash,
    or feature detector result types.
    """

    evidence_id: EvidenceId
    frame_id: FrameId
    source_id: str
    kind: EvidenceKind
    score: float
    roi_root: Rect
    provenance: EvidenceProvenance
    result: ResultT
    bounds_root: Rect | None = None
    duration: timedelta | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.evidence_id, EvidenceId):
            raise TypeError("evidence_id must be EvidenceId")
        if not isinstance(self.frame_id, FrameId):
            raise TypeError("evidence frame_id must be FrameId")
        if not isinstance(self.kind, EvidenceKind):
            raise TypeError("evidence kind must be EvidenceKind")
        if not isinstance(self.roi_root, Rect):
            raise TypeError("evidence roi_root must be Rect")
        if not isinstance(self.provenance, EvidenceProvenance):
            raise TypeError(
                "evidence provenance must be EvidenceProvenance"
            )
        if self.bounds_root is not None and not isinstance(
            self.bounds_root,
            Rect,
        ):
            raise TypeError(
                "evidence bounds_root must be Rect or None"
            )
        if (
            self.bounds_root is not None
            and not self.roi_root.contains_rect(self.bounds_root)
        ):
            raise ValueError(
                "evidence bounds_root must be contained by roi_root"
            )

        duration = self.duration
        if duration is not None:
            if not isinstance(duration, timedelta):
                raise TypeError(
                    "evidence duration must be timedelta or None"
                )
            if duration < timedelta(0):
                raise ValueError(
                    "evidence duration cannot be negative"
                )

        object.__setattr__(
            self,
            "source_id",
            _normalize_non_empty_text(
                self.source_id,
                field_name="evidence source id",
            ),
        )
        object.__setattr__(
            self,
            "score",
            _normalize_unit_score(self.score),
        )


@dataclass(frozen=True, slots=True)
class EvidenceSet:
    """Immutable evidence collection for exactly one captured frame."""

    frame_id: FrameId
    source_id: str
    root_bounds: Rect
    items: tuple[Evidence[object], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not isinstance(self.frame_id, FrameId):
            raise TypeError("evidence set frame_id must be FrameId")
        if not isinstance(self.root_bounds, Rect):
            raise TypeError("evidence set root_bounds must be Rect")
        if not isinstance(self.items, tuple):
            raise TypeError("evidence set items must be a tuple")

        source_id = _normalize_non_empty_text(
            self.source_id,
            field_name="evidence set source id",
        )
        seen_ids: set[EvidenceId] = set()

        for index, evidence in enumerate(self.items):
            if not isinstance(evidence, Evidence):
                raise TypeError(
                    f"evidence set items[{index}] must be Evidence, "
                    f"got {type(evidence).__name__}"
                )
            if evidence.evidence_id in seen_ids:
                raise ValueError(
                    "evidence set cannot contain duplicate evidence ids: "
                    f"{evidence.evidence_id!s}"
                )
            if evidence.frame_id != self.frame_id:
                raise ValueError(
                    "evidence frame_id must match evidence set frame_id"
                )
            if evidence.source_id != source_id:
                raise ValueError(
                    "evidence source_id must match evidence set source_id"
                )
            if not self.root_bounds.contains_rect(evidence.roi_root):
                raise ValueError(
                    "evidence roi_root must be contained by "
                    "evidence set root_bounds"
                )
            seen_ids.add(evidence.evidence_id)

        object.__setattr__(self, "source_id", source_id)

    def get(
        self,
        evidence_id: EvidenceId,
    ) -> Evidence[object] | None:
        if not isinstance(evidence_id, EvidenceId):
            raise TypeError("evidence_id must be EvidenceId")

        for evidence in self.items:
            if evidence.evidence_id == evidence_id:
                return evidence

        return None

    def of_kind(
        self,
        kind: EvidenceKind,
    ) -> tuple[Evidence[object], ...]:
        if not isinstance(kind, EvidenceKind):
            raise TypeError("kind must be EvidenceKind")

        return tuple(
            evidence
            for evidence in self.items
            if evidence.kind == kind
        )

    def from_detector(
        self,
        detector_id: str,
    ) -> tuple[Evidence[object], ...]:
        normalized_detector_id = _normalize_non_empty_text(
            detector_id,
            field_name="detector id",
        )
        return tuple(
            evidence
            for evidence in self.items
            if evidence.provenance.detector_id
            == normalized_detector_id
        )

    def best(
        self,
        *,
        kind: EvidenceKind | None = None,
    ) -> Evidence[object] | None:
        if kind is not None and not isinstance(kind, EvidenceKind):
            raise TypeError("kind must be EvidenceKind or None")

        candidates = (
            self.items
            if kind is None
            else self.of_kind(kind)
        )
        if not candidates:
            return None

        return max(
            candidates,
            key=lambda evidence: evidence.score,
        )

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self):
        return iter(self.items)

    def __bool__(self) -> bool:
        return bool(self.items)
