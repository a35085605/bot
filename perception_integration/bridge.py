from __future__ import annotations

from datetime import timedelta
from typing import TypeVar

from detector_input import DetectorInputContext
from evidence.domain.models import (
    Evidence,
    EvidenceId,
    EvidenceKind,
    EvidenceProvenance,
)
from geometry.rect import Rect


ResultT = TypeVar("ResultT")


class EvidenceAssembler:
    """Pure bridge from detector-local output to contextualized Evidence."""

    @staticmethod
    def assemble(
        *,
        context: DetectorInputContext,
        evidence_id: EvidenceId,
        kind: EvidenceKind,
        score: float,
        provenance: EvidenceProvenance,
        result: ResultT,
        bounds_local: Rect | None = None,
        duration: timedelta | None = None,
    ) -> Evidence[ResultT]:
        if not isinstance(context, DetectorInputContext):
            raise TypeError("context must be DetectorInputContext")

        bounds_root = (
            None
            if bounds_local is None
            else context.local_rect_to_root(bounds_local)
        )

        return Evidence(
            evidence_id=evidence_id,
            frame_id=context.frame_id,
            source_id=context.source_id,
            kind=kind,
            score=score,
            roi_root=context.roi_root,
            bounds_root=bounds_root,
            provenance=provenance,
            result=result,
            duration=duration,
        )
