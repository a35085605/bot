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
    or shares memory with its backing image.
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
    """Return a zero-copy local raster view.

    Nested crops are flattened directly onto the owned backing image without
    exposing backing placement as part of the public raster contract.
    """

    source = _validate_source(image)
    if not isinstance(bounds, Rect):
        raise TypeError("bounds must be Rect")
    if not source.bounds.contains_rect(bounds):
        raise ValueError("bounds must be contained by source image")

    if isinstance(source, RasterImage):
        backing_image = source
        bounds_in_backing = bounds
    else:
        backing_image = source._backing_image
        parent_bounds = source._bounds_in_backing
        bounds_in_backing = bounds.translated(
            dx=parent_bounds.left,
            dy=parent_bounds.top,
        )

    return RasterImageView._from_backing(
        backing_image=backing_image,
        bounds_in_backing=bounds_in_backing,
    )
