from __future__ import annotations

from geometry.rect import Rect
from imaging.models import RasterImage


def crop_image(image: RasterImage, *, bounds: Rect) -> RasterImage:
    """Return an independently owned crop using image-local coordinates."""

    if not isinstance(image, RasterImage):
        raise TypeError("image must be RasterImage")
    if not isinstance(bounds, Rect):
        raise TypeError("bounds must be Rect")
    if not image.bounds.contains_rect(bounds):
        raise ValueError("crop bounds must be contained by image bounds")

    if image.pixels.ndim == 2:
        pixels = image.pixels[
            bounds.top:bounds.bottom,
            bounds.left:bounds.right,
        ]
    else:
        pixels = image.pixels[
            bounds.top:bounds.bottom,
            bounds.left:bounds.right,
            :,
        ]

    return RasterImage(pixels=pixels)
