from __future__ import annotations

from typing import Protocol

from extensions.vision.template_matching.domain.models import (
    GrayImage,
    MatchTemplate,
)
from extensions.vision.template_matching.domain.results import MatchCandidate


class TemplateMatchEngine(Protocol):
    def match(
        self,
        image: GrayImage,
        template: MatchTemplate,
        *,
        candidate_floor: float,
    ) -> tuple[MatchCandidate, ...]:
        """
        Extract normalized candidates whose scores are greater than
        or equal to candidate_floor.

        candidate_floor is a candidate collection boundary, not a
        business acceptance threshold.

        Contract:

        - candidate_floor must be finite and within [0.0, 1.0].
        - candidate scores must be finite and within [0.0, 1.0].
        - higher scores represent better matches.
        - every returned candidate must have
          score >= candidate_floor.
        - candidate rectangles use image-local pixel coordinates.
        - candidates may overlap or represent the same occurrence.
        - candidate ordering is unspecified.

        Acceptance decisions, overlap suppression and final result
        interpretation are handled outside the engine.
        """
        ...
