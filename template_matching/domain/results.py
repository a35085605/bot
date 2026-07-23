from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from geometry.rect import Rect
from template_matching.domain.keys import normalize_template_key
from template_matching.domain.scores import normalize_unit_score


def _normalize_candidates(
    candidates: Iterable[MatchCandidate],
    *,
    field_name: str,
) -> tuple[MatchCandidate, ...]:
    if isinstance(candidates, (str, bytes, bytearray)):
        raise TypeError(
            f"{field_name} must be an iterable of MatchCandidate"
        )

    try:
        normalized = tuple(candidates)
    except TypeError as exc:
        raise TypeError(
            f"{field_name} must be iterable"
        ) from exc

    for index, candidate in enumerate(normalized):
        if not isinstance(candidate, MatchCandidate):
            raise TypeError(
                f"{field_name}[{index}] must be MatchCandidate, "
                f"got {type(candidate).__name__}"
            )

    return normalized


@dataclass(frozen=True, slots=True)
class MatchCandidate:
    score: float
    rect: Rect

    def __post_init__(self) -> None:
        score = normalize_unit_score(
            self.score,
            field_name="candidate score",
        )

        if not isinstance(self.rect, Rect):
            raise TypeError(
                "candidate rect must be Rect, "
                f"got {type(self.rect).__name__}"
            )

        object.__setattr__(
            self,
            "score",
            score,
        )


@dataclass(frozen=True, slots=True)
class TemplateMatchResult:
    """
    Post-suppression template matching result.

    retained_candidates contains candidates that:

    - were collected by the matching engine at or above
      candidate_floor; and
    - survived the configured suppression policy.

    Candidates removed by suppression are not retained.

    When the suppression policy limits the result count, this result
    also does not guarantee that every engine candidate at or above
    candidate_floor is present.
    """

    template_key: str
    candidate_floor: float
    retained_candidates: tuple[MatchCandidate, ...] = field(
        default_factory=tuple
    )

    def __post_init__(self) -> None:
        template_key = normalize_template_key(
            self.template_key
        )

        candidate_floor = normalize_unit_score(
            self.candidate_floor,
            field_name="candidate_floor",
        )

        retained_candidates = _normalize_candidates(
            self.retained_candidates,
            field_name="retained_candidates",
        )

        below_candidate_floor = tuple(
            candidate
            for candidate in retained_candidates
            if candidate.score < candidate_floor
        )

        if below_candidate_floor:
            lowest_score = min(
                candidate.score
                for candidate in below_candidate_floor
            )

            raise ValueError(
                "template match result cannot retain candidates "
                "below candidate_floor: "
                f"candidate_floor={candidate_floor}, "
                f"lowest_score={lowest_score}"
            )

        object.__setattr__(
            self,
            "template_key",
            template_key,
        )
        object.__setattr__(
            self,
            "candidate_floor",
            candidate_floor,
        )
        object.__setattr__(
            self,
            "retained_candidates",
            retained_candidates,
        )

    @classmethod
    def from_retained_candidates(
        cls,
        *,
        template_key: str,
        candidate_floor: float,
        retained_candidates: Iterable[MatchCandidate],
    ) -> TemplateMatchResult:
        return cls(
            template_key=template_key,
            candidate_floor=candidate_floor,
            retained_candidates=tuple(retained_candidates),
        )

    @property
    def best_candidate(self) -> MatchCandidate | None:
        """
        Highest-scoring candidate retained after suppression.

        The candidate has not necessarily passed a use-case threshold.
        """
        if not self.retained_candidates:
            return None

        return max(
            self.retained_candidates,
            key=lambda candidate: candidate.score,
        )

    def accepted_by(
        self,
        threshold: float,
    ) -> tuple[MatchCandidate, ...]:
        """
        Return retained candidates accepted by threshold.

        threshold cannot be below candidate_floor because candidates
        below candidate_floor were not collected by the engine.
        """
        threshold = normalize_unit_score(
            threshold,
            field_name="threshold",
        )

        if threshold < self.candidate_floor:
            raise ValueError(
                "threshold cannot be below the candidate_floor used "
                "to collect this result: "
                f"threshold={threshold}, "
                f"candidate_floor={self.candidate_floor}"
            )

        return tuple(
            candidate
            for candidate in self.retained_candidates
            if candidate.score >= threshold
        )


@dataclass(frozen=True, slots=True)
class EvaluatedMatches:
    """
    Threshold evaluation over a post-suppression match result.

    accepted_matches contains retained candidates whose scores are
    greater than or equal to threshold.

    rejected_candidates contains retained candidates below threshold.
    It does not include candidates removed by suppression.
    """

    match_result: TemplateMatchResult = field(
        repr=False
    )
    threshold: float
    accepted_matches: tuple[MatchCandidate, ...] = field(
        init=False
    )

    def __post_init__(self) -> None:
        if not isinstance(
            self.match_result,
            TemplateMatchResult,
        ):
            raise TypeError(
                "match_result must be TemplateMatchResult, "
                f"got {type(self.match_result).__name__}"
            )

        threshold = normalize_unit_score(
            self.threshold,
            field_name="threshold",
        )

        accepted_matches = self.match_result.accepted_by(
            threshold
        )

        object.__setattr__(
            self,
            "threshold",
            threshold,
        )
        object.__setattr__(
            self,
            "accepted_matches",
            accepted_matches,
        )

    @classmethod
    def from_result(
        cls,
        result: TemplateMatchResult,
        *,
        threshold: float,
    ) -> EvaluatedMatches:
        return cls(
            match_result=result,
            threshold=threshold,
        )

    @property
    def template_key(self) -> str:
        return self.match_result.template_key

    @property
    def candidate_floor(self) -> float:
        return self.match_result.candidate_floor

    @property
    def retained_candidates(
        self,
    ) -> tuple[MatchCandidate, ...]:
        """
        Candidates retained after suppression.
        """
        return self.match_result.retained_candidates

    @property
    def rejected_candidates(
        self,
    ) -> tuple[MatchCandidate, ...]:
        """
        Retained candidates that did not reach threshold.
        """
        return tuple(
            candidate
            for candidate in self.retained_candidates
            if candidate.score < self.threshold
        )

    @property
    def best_match(self) -> MatchCandidate | None:
        """
        Highest-scoring accepted match.
        """
        if not self.accepted_matches:
            return None

        return max(
            self.accepted_matches,
            key=lambda candidate: candidate.score,
        )

    @property
    def best_candidate(self) -> MatchCandidate | None:
        """
        Highest-scoring candidate retained after suppression,
        whether accepted or rejected.
        """
        return self.match_result.best_candidate

    @property
    def success(self) -> bool:
        return bool(self.accepted_matches)

    def __len__(self) -> int:
        return len(self.accepted_matches)

    def __iter__(self):
        return iter(self.accepted_matches)

    def __bool__(self) -> bool:
        return self.success
