from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from numbers import Integral
from typing import Protocol

from extensions.vision.template_matching.domain.results import MatchCandidate
from extensions.vision.template_matching.domain.scores import normalize_unit_score


class MatchSuppressionPolicy(Protocol):
    """
    Domain policy for reducing raw match candidates to distinct matches.

    Implementations must:

    - return only candidates from the provided input;
    - return candidates in deterministic order from highest to
      lowest score;
    - be score-monotonic: adding candidates with lower scores must
      not cause a higher-scoring selected candidate to be removed.

    Score monotonicity ensures that collecting additional candidates
    below an evaluation threshold does not change which higher-scoring
    candidates survive suppression.
    """

    def suppress(
        self,
        candidates: Iterable[MatchCandidate],
    ) -> tuple[MatchCandidate, ...]:
        ...


@dataclass(frozen=True, slots=True)
class GreedyIoUNms:
    """
    Greedy intersection-over-union non-maximum suppression.

    Candidates are processed from highest to lowest score. A candidate is
    suppressed when its IoU with an already selected candidate is strictly
    greater than ``iou_threshold``.

    The strict comparison gives the boundary values these meanings:

    - ``iou_threshold=0.0`` suppresses candidates with any positive overlap;
    - ``iou_threshold=1.0`` disables overlap-based suppression because IoU
      cannot be greater than 1.0.
    """

    iou_threshold: float = 0.3
    max_candidates: int | None = None

    def __post_init__(self) -> None:
        iou_threshold = normalize_unit_score(
            self.iou_threshold,
            field_name="iou_threshold",
        )

        max_candidates = self.max_candidates

        if max_candidates is not None:
            if (
                isinstance(max_candidates, bool)
                or not isinstance(max_candidates, Integral)
            ):
                raise TypeError(
                    "max_candidates must be an integer or None"
                )

            max_candidates = int(max_candidates)

            if max_candidates <= 0:
                raise ValueError(
                    "max_candidates must be greater than zero"
                )

        object.__setattr__(
            self,
            "iou_threshold",
            iou_threshold,
        )
        object.__setattr__(
            self,
            "max_candidates",
            max_candidates,
        )

    def suppress(
        self,
        candidates: Iterable[MatchCandidate],
    ) -> tuple[MatchCandidate, ...]:
        normalized = self._normalize_candidates(candidates)
        ordered = sorted(
            normalized,
            key=self._sorting_key,
        )

        selected: list[MatchCandidate] = []

        for candidate in ordered:
            overlaps_selected = any(
                candidate.rect.iou(existing.rect)
                > self.iou_threshold
                for existing in selected
            )

            if overlaps_selected:
                continue

            selected.append(candidate)

            if (
                self.max_candidates is not None
                and len(selected) >= self.max_candidates
            ):
                break

        return tuple(selected)

    @staticmethod
    def _normalize_candidates(
        candidates: Iterable[MatchCandidate],
    ) -> tuple[MatchCandidate, ...]:
        if isinstance(candidates, (str, bytes, bytearray)):
            raise TypeError(
                "candidates must be an iterable of MatchCandidate"
            )

        try:
            normalized = tuple(candidates)
        except TypeError as exc:
            raise TypeError(
                "candidates must be iterable"
            ) from exc

        for index, candidate in enumerate(normalized):
            if not isinstance(candidate, MatchCandidate):
                raise TypeError(
                    f"candidates[{index}] must be MatchCandidate, "
                    f"got {type(candidate).__name__}"
                )

        return normalized

    @staticmethod
    def _sorting_key(
        candidate: MatchCandidate,
    ) -> tuple[float, int, int, int, int]:
        return (
            -candidate.score,
            candidate.rect.y,
            candidate.rect.x,
            candidate.rect.width,
            candidate.rect.height,
        )
