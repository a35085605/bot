from __future__ import annotations

from geometry.rect import Rect
from imaging.models import RasterImage, RasterImageView, _slice_pixels


RasterSource = RasterImage | RasterImageView


def _validate_source(image: object) -> RasterSource:
    if not isinstance(image, (RasterImage, RasterImageView)):
        raise TypeError("image must be RasterImage or RasterImageView")
    return image


def crop_image(image: RasterSource, *, bounds: Rect) -> RasterImage:
    """Return an independently owned crop using image-local coordinates."""

    source = _validate_source(image)
    if not isinstance(bounds, Rect):
        raise TypeError("bounds must be Rect")
    if not source.bounds.contains_rect(bounds):
        raise ValueError("crop bounds must be contained by image bounds")

    return RasterImage(
        pixels=_slice_pixels(source.pixels, bounds=bounds),
        pixel_format=source.pixel_format,
    )


def crop_image_view(
    image: RasterSource,
    *,
    bounds: Rect,
) -> RasterImageView:
    """Return a zero-copy crop flattened onto the root raster."""

    source = _validate_source(image)
    return source.view(bounds)
