from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

from geometry.rect import Rect
from geometry.size import Size
from imaging import ImagePixels, Interpolation, RasterImage
from observation.capture import FrameId


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
    """Spatial correspondence between a detector image and a root-space ROI."""

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

        left = source.left + relative_left * source.width // content.width
        top = source.top + relative_top * source.height // content.height
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
    """Observation identity and placement for one detector invocation."""

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


@dataclass(frozen=True, slots=True)
class PreparationProvenance:
    """How one source ROI became the detector raster."""

    source_size: Size
    output_size: Size
    interpolation: Interpolation

    def __post_init__(self) -> None:
        if not isinstance(self.source_size, Size):
            raise TypeError("source_size must be Size")
        if not isinstance(self.output_size, Size):
            raise TypeError("output_size must be Size")
        if not isinstance(self.interpolation, Interpolation):
            raise TypeError("interpolation must be Interpolation")

    @property
    def resized(self) -> bool:
        return self.source_size != self.output_size


@dataclass(frozen=True, slots=True)
class PreparedDetectorInput:
    """Detector-ready raster paired with its root-space placement."""

    image: RasterImage
    context: DetectorInputContext
    provenance: PreparationProvenance

    def __post_init__(self) -> None:
        if not isinstance(self.image, RasterImage):
            raise TypeError("prepared image must be RasterImage")
        if not isinstance(self.context, DetectorInputContext):
            raise TypeError("context must be DetectorInputContext")
        if not isinstance(self.provenance, PreparationProvenance):
            raise TypeError("provenance must be PreparationProvenance")
        if self.image.size != self.provenance.output_size:
            raise ValueError(
                "prepared image size must match provenance output_size"
            )
        input_bounds = self.context.placement.input_bounds_local
        if (
            input_bounds.width != self.image.width
            or input_bounds.height != self.image.height
        ):
            raise ValueError(
                "prepared image size must match placement input bounds"
            )

    @property
    def pixels(self) -> ImagePixels:
        return self.image.pixels


DetectorImage: TypeAlias = RasterImage
