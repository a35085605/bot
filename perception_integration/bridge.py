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
class ImagePlacement:
    """
    Spatial correspondence between one detector image and one frame-root ROI.

    ``input_bounds_local`` describes the complete image passed to a detector.
    Its origin must be ``(0, 0)``. ``content_bounds_local`` describes the
    detector-image region containing pixels derived from the captured frame.
    The remaining area may be synthetic padding or letterboxing.

    ``source_bounds_root`` is the frame-root region represented by
    ``content_bounds_local``. The two rectangles may have different sizes when
    input preparation resized the source ROI.
    """

    input_bounds_local: Rect
    content_bounds_local: Rect
    source_bounds_root: Rect

    def __post_init__(self) -> None:
        if not isinstance(self.input_bounds_local, Rect):
            raise TypeError("input_bounds_local must be Rect")
        if not isinstance(self.content_bounds_local, Rect):
            raise TypeError("content_bounds_local must be Rect")
        if not isinstance(self.source_bounds_root, Rect):
            raise TypeError("source_bounds_root must be Rect")
        if (
            self.input_bounds_local.left != 0
            or self.input_bounds_local.top != 0
        ):
            raise ValueError("input_bounds_local must start at (0, 0)")
        if not self.input_bounds_local.contains_rect(
            self.content_bounds_local
        ):
            raise ValueError(
                "content_bounds_local must be contained by "
                "input_bounds_local"
            )

    def local_rect_to_root(self, rect: Rect) -> Rect:
        """
        Map a detector-local rectangle into frame-root coordinates.

        Results must be fully contained by ``content_bounds_local``. This
        rejects detections that fall in synthetic padding. Leading edges round
        down and trailing edges round up so the mapped integer rectangle
        contains the complete detector result.
        """
        if not isinstance(rect, Rect):
            raise TypeError("detector-local rect must be Rect")
        if not self.content_bounds_local.contains_rect(rect):
            raise ValueError(
                "detector-local rect must be contained by "
                "content_bounds_local"
            )

        content = self.content_bounds_local
        source = self.source_bounds_root

        relative_left = rect.left - content.left
        relative_top = rect.top - content.top
        relative_right = rect.right - content.left
        relative_bottom = rect.bottom - content.top

        left = source.left + (
            relative_left * source.width // content.width
        )
        top = source.top + (
            relative_top * source.height // content.height
        )
        right = source.left + _ceil_div(
            relative_right * source.width,
            content.width,
        )
        bottom = source.top + _ceil_div(
            relative_bottom * source.height,
            content.height,
        )

        return Rect.from_ltrb(
            left=left,
            top=top,
            right=right,
            bottom=bottom,
        )


@dataclass(frozen=True, slots=True)
class DetectorInputContext:
    """
    Observation identity and image placement for one detector invocation.

    This integration DTO deliberately contains no pixels, window metadata,
    screen coordinates, capture backend, detector implementation, or
    scheduling policy.
    """

    frame_id: FrameId
    source_id: str
    root_bounds: Rect
    placement: ImagePlacement

    def __post_init__(self) -> None:
        if not isinstance(self.frame_id, FrameId):
            raise TypeError("detector context frame_id must be FrameId")
        if not isinstance(self.root_bounds, Rect):
            raise TypeError("detector context root_bounds must be Rect")
        if not isinstance(self.placement, ImagePlacement):
            raise TypeError("detector context placement must be ImagePlacement")
        if not self.root_bounds.contains_rect(
            self.placement.source_bounds_root
        ):
            raise ValueError(
                "detector source bounds must be contained by root_bounds"
            )

        object.__setattr__(
            self,
            "source_id",
            _normalize_non_empty_text(
                self.source_id,
                field_name="detector context source id",
            ),
        )

    @property
    def roi_root(self) -> Rect:
        return self.placement.source_bounds_root

    def local_rect_to_root(self, rect: Rect) -> Rect:
        return self.placement.local_rect_to_root(rect)


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
