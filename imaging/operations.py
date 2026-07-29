from __future__ import annotations

from geometry.rect import Rect
from imaging.models import RasterImage, RasterImageView


RasterSource = RasterImage | RasterImageView


def _validate_source(image: object) -> RasterSource:
    if not isinstance(image, (RasterImage, RasterImageView)):
        raise TypeError("image must be RasterImage or RasterImageView")
    return image


def materialize_image(image: RasterSource) -> RasterImage:
    """Return an independently owned immutable raster.

    An existing ``RasterImage`` already owns its pixels and is returned
    unchanged. A ``RasterImageView`` is copied so the result no longer retains
    or shares memory with the root raster.
    """

    source = _validate_source(image)
    if isinstance(source, RasterImage):
        return source

    return RasterImage(
        pixels=source.pixels,
        pixel_format=source.pixel_format,
    )


def crop_image(image: RasterSource, *, bounds: Rect) -> RasterImage:
    """Return an independently owned crop using image-local coordinates."""

    return materialize_image(crop_image_view(image, bounds=bounds))


def crop_image_view(
    image: RasterSource,
    *,
    bounds: Rect,
) -> RasterImageView:
    """Return a zero-copy crop flattened onto the root raster."""

    source = _validate_source(image)
    return source.view(bounds)
