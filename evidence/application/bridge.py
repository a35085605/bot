from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import TypeVar

from evidence.domain.models import (
    Evidence,
    EvidenceId,
    EvidenceKind,
    EvidenceProvenance,
)
from geometry.rect import Rect
from observation import FrameId


ResultT = TypeVar("ResultT")


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


def _ceil_div(numerator: int, denominator: int) -> int:
    return (numerator + denominator - 1) // denominator


@dataclass(frozen=True, slots=True)
class DetectorInputContext:
    """
    Observation context required to place detector-local output in root space.

    ``input_bounds_local`` describes the exact image passed to a detector. Its
    origin must be ``(0, 0)``. ``roi_root`` describes the corresponding region
    in the captured frame's root coordinate space. The two rectangles may have
    different sizes when input preparation resized the ROI.

    The context deliberately contains no pixels, window metadata, screen
    coordinates, capture backend, detector implementation, or scheduling
    policy. Preparing the detector image and declaring this correspondence are
    responsibilities of the integration caller.
    """

    frame_id: FrameId
    source_id: str
    root_bounds: Rect
    roi_root: Rect
    input_bounds_local: Rect

    def __post_init__(self) -> None:
        if not isinstance(self.frame_id, FrameId):
            raise TypeError("detector context frame_id must be FrameId")
        if not isinstance(self.root_bounds, Rect):
            raise TypeError("detector context root_bounds must be Rect")
        if not isinstance(self.roi_root, Rect):
            raise TypeError("detector context roi_root must be Rect")
        if not isinstance(self.input_bounds_local, Rect):
            raise TypeError(
                "detector context input_bounds_local must be Rect"
            )
        if not self.root_bounds.contains_rect(self.roi_root):
            raise ValueError(
                "detector context roi_root must be contained by root_bounds"
            )
        if (
            self.input_bounds_local.left != 0
            or self.input_bounds_local.top != 0
        ):
            raise ValueError(
                "detector context input_bounds_local must start at (0, 0)"
            )

        object.__setattr__(
            self,
            "source_id",
            _normalize_non_empty_text(
                self.source_id,
                field_name="detector context source id",
            ),
        )

    def local_rect_to_root(self, rect: Rect) -> Rect:
        """
        Map a half-open detector-local rectangle into frame root space.

        Leading edges are rounded down and trailing edges are rounded up. The
        resulting integer rectangle therefore contains the complete mapped
        detector rectangle, including when the detector input was resized.
        """
        if not isinstance(rect, Rect):
            raise TypeError("detector-local rect must be Rect")
        if not self.input_bounds_local.contains_rect(rect):
            raise ValueError(
                "detector-local rect must be contained by "
                "input_bounds_local"
            )

        input_width = self.input_bounds_local.width
        input_height = self.input_bounds_local.height

        left = self.roi_root.left + (
            rect.left * self.roi_root.width // input_width
        )
        top = self.roi_root.top + (
            rect.top * self.roi_root.height // input_height
        )
        right = self.roi_root.left + _ceil_div(
            rect.right * self.roi_root.width,
            input_width,
        )
        bottom = self.roi_root.top + _ceil_div(
            rect.bottom * self.roi_root.height,
            input_height,
        )

        return Rect.from_ltrb(
            left=left,
            top=top,
            right=right,
            bottom=bottom,
        )


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
