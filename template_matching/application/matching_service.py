from __future__ import annotations

import numpy as np

from template_matching.domain.models import (
    GrayImage,
    Template,
)
from template_matching.domain.results import (
    EvaluatedMatches,
    MatchCandidate,
    TemplateMatchResult,
)
from template_matching.domain.scores import normalize_unit_score
from template_matching.domain.suppression import (
    MatchSuppressionPolicy,
)
from template_matching.ports.engine import TemplateMatchEngine
from template_matching.ports.repository import TemplateRepository


class TemplateMatchingService:
    def __init__(
        self,
        repository: TemplateRepository,
        engine: TemplateMatchEngine,
        suppression: MatchSuppressionPolicy,
    ) -> None:
        self._repository = repository
        self._engine = engine
        self._suppression = suppression

    def match(
        self,
        image: GrayImage,
        template_key: str,
        *,
        candidate_floor: float,
    ) -> TemplateMatchResult:
        """
        Collect matching candidates.

        candidate_floor controls candidate collection only. It does not
        determine whether a candidate should be accepted by a use case.
        """
        self._validate_image(image)

        candidate_floor = normalize_unit_score(
            candidate_floor,
            field_name="candidate_floor",
        )

        template = self._repository.require(template_key)

        if (
            template.width > image.shape[1]
            or template.height > image.shape[0]
        ):
            return TemplateMatchResult(
                template_key=template.key,
                candidate_floor=candidate_floor,
            )

        raw_candidates = self._engine.match(
            image=image,
            template=template,
            candidate_floor=candidate_floor,
        )

        candidates = self._validate_engine_candidates(
            candidates=raw_candidates,
            image=image,
            template=template,
            candidate_floor=candidate_floor,
        )

        suppressed = self._suppression.suppress(
            candidates
        )

        return TemplateMatchResult.from_retained_candidates(
            template_key=template.key,
            candidate_floor=candidate_floor,
            retained_candidates=suppressed,
        )

    def evaluate(
        self,
        image: GrayImage,
        template_key: str,
        *,
        threshold: float,
        candidate_floor: float | None = None,
    ) -> EvaluatedMatches:
        """
        Collect, suppress and evaluate template match candidates.

        When candidate_floor is omitted, it defaults to threshold.
        This avoids collecting candidates that the caller does not need.

        candidate_floor must not exceed threshold because doing so would
        omit candidates that should be accepted by threshold.
        """

        threshold = normalize_unit_score(
            threshold,
            field_name="threshold",
        )

        if candidate_floor is None:
            normalized_candidate_floor = threshold
        else:
            normalized_candidate_floor = normalize_unit_score(
                candidate_floor,
                field_name="candidate_floor",
            )

        if normalized_candidate_floor > threshold:
            raise ValueError(
                "candidate_floor cannot exceed threshold: "
                f"candidate_floor={normalized_candidate_floor}, "
                f"threshold={threshold}"
            )

        result = self.match(
            image=image,
            template_key=template_key,
            candidate_floor=normalized_candidate_floor,
        )

        return EvaluatedMatches.from_result(
            result,
            threshold=threshold,
        )

    @staticmethod
    def _validate_image(
        image: GrayImage,
    ) -> None:
        if not isinstance(image, np.ndarray):
            raise TypeError(
                "matching image must be a numpy array"
            )

        if image.dtype != np.uint8:
            raise TypeError(
                "matching image must be uint8, "
                f"got {image.dtype}"
            )

        if image.ndim != 2:
            raise ValueError(
                "matching image must be 2D grayscale, "
                f"got shape {image.shape}"
            )

        if image.size == 0:
            raise ValueError(
                "matching image cannot be empty"
            )

    @staticmethod
    def _validate_engine_candidates(
        *,
        candidates: object,
        image: GrayImage,
        template: Template,
        candidate_floor: float,
    ) -> tuple[MatchCandidate, ...]:
        if not isinstance(candidates, tuple):
            raise TypeError(
                "template match engine must return "
                "tuple[MatchCandidate, ...]"
            )

        image_height, image_width = image.shape
        validated: list[MatchCandidate] = []

        for index, candidate in enumerate(candidates):
            if not isinstance(candidate, MatchCandidate):
                raise TypeError(
                    f"engine result[{index}] must be "
                    "MatchCandidate, "
                    f"got {type(candidate).__name__}"
                )

            if candidate.score < candidate_floor:
                raise ValueError(
                    f"engine result[{index}] score is below "
                    "candidate_floor: "
                    f"score={candidate.score}, "
                    f"candidate_floor={candidate_floor}"
                )

            rect = candidate.rect

            if (
                rect.width != template.width
                or rect.height != template.height
            ):
                raise ValueError(
                    f"engine result[{index}] has unexpected "
                    "rectangle size: "
                    f"expected={template.width}x{template.height}, "
                    f"got={rect.width}x{rect.height}"
                )

            if rect.x < 0 or rect.y < 0:
                raise ValueError(
                    f"engine result[{index}] has negative "
                    f"coordinates: ({rect.x}, {rect.y})"
                )

            if (
                rect.right > image_width
                or rect.bottom > image_height
            ):
                raise ValueError(
                    f"engine result[{index}] is outside "
                    "the matching image"
                )

            validated.append(candidate)

        return tuple(validated)
