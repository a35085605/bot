from __future__ import annotations

from imaging import PixelFormat
from vision.reference_assets.domain.models import ReferenceImage
from vision.template_matching.domain.models import MatchTemplate


class ReferenceMatchTemplateFactory:
    """Adapt a reference asset into detector-local matching pixels."""

    def create(self, asset: ReferenceImage) -> MatchTemplate:
        if not isinstance(asset, ReferenceImage):
            raise TypeError("asset must be ReferenceImage")
        if asset.pixel_format is not PixelFormat.GRAY8:
            raise ValueError(
                "template matching requires a GRAY8 reference asset, "
                f"got {asset.pixel_format.value}"
            )

        return MatchTemplate(
            gray=asset.pixels,
            mask=asset.coverage_mask,
        )
