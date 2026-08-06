from __future__ import annotations

from detector_input.models import (
    DetectorInputContext,
    ImagePlacement,
    PreparationProvenance,
    PreparedDetectorInput,
)
from geometry.rect import Rect
from geometry.size import Size
from imaging import (
    ImageResizer,
    Interpolation,
    RasterImage,
    crop_image,
)
from observation.capture import FrameId


class FixedViewportRoiPreparer:
    """Prepare a detector raster from a resolved canonical viewport-root ROI."""

    def __init__(self, *, resizer: ImageResizer) -> None:
        if not hasattr(resizer, "resize"):
            raise TypeError("resizer must provide resize()")
        self._resizer = resizer

    def prepare(
        self,
        *,
        frame_id: FrameId,
        source_id: str,
        root_bounds: Rect,
        image: RasterImage,
        roi_root: Rect,
        output_size: Size,
        interpolation: Interpolation = Interpolation.LINEAR,
    ) -> PreparedDetectorInput:
        if not isinstance(frame_id, FrameId):
            raise TypeError("frame_id must be FrameId")
        if not isinstance(root_bounds, Rect):
            raise TypeError("root_bounds must be Rect")
        if not isinstance(image, RasterImage):
            raise TypeError("image must be RasterImage")
        if not isinstance(roi_root, Rect):
            raise TypeError("roi_root must be Rect")
        if not isinstance(output_size, Size):
            raise TypeError("output_size must be Size")
        if not isinstance(interpolation, Interpolation):
            raise TypeError("interpolation must be Interpolation")
        if image.width != root_bounds.width or image.height != root_bounds.height:
            raise ValueError(
                "source image size must match canonical viewport root bounds"
            )
        if not root_bounds.contains_rect(roi_root):
            raise ValueError(
                "roi_root must be contained by canonical viewport root bounds"
            )

        image_local_roi = roi_root.translated(
            dx=-root_bounds.left,
            dy=-root_bounds.top,
        )
        cropped = crop_image(image, bounds=image_local_roi)
        prepared = (
            cropped
            if cropped.size == output_size
            else self._resizer.resize(
                cropped,
                target_size=output_size,
                interpolation=interpolation,
            )
        )

        input_bounds = Rect(
            x=0,
            y=0,
            width=prepared.width,
            height=prepared.height,
        )
        placement = ImagePlacement(
            input_bounds_local=input_bounds,
            content_bounds_local=input_bounds,
            source_bounds_root=roi_root,
        )
        return PreparedDetectorInput(
            image=prepared,
            context=DetectorInputContext(
                frame_id=frame_id,
                source_id=source_id,
                root_bounds=root_bounds,
                placement=placement,
            ),
            provenance=PreparationProvenance(
                source_size=cropped.size,
                output_size=prepared.size,
                interpolation=interpolation,
            ),
        )
