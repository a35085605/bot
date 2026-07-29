from __future__ import annotations

from dataclasses import dataclass, field
import numpy as np
import numpy.typing as npt

from imaging import PixelFormat, RasterImage, materialize_image
from vision.reference_assets.domain.keys import (
    normalize_reference_asset_key,
)


CoverageMask = npt.NDArray[np.uint8]


# Backward-compatible name; the format is owned by imaging.
ReferenceImageFormat = PixelFormat


def _freeze_coverage_mask(
    value: object,
    *,
    expected_shape: tuple[int, int],
) -> CoverageMask:
    if not isinstance(value, np.ndarray):
        raise TypeError("coverage mask must be a numpy array")
    if value.dtype != np.uint8:
        raise TypeError(
            "coverage mask must be uint8, "
            f"got {value.dtype}"
        )
    if value.ndim != 2 or value.shape != expected_shape:
        raise ValueError(
            "coverage mask shape must match reference image dimensions"
        )

    binary = np.where(
        value != 0,
        255,
        0,
    ).astype(np.uint8, copy=False)
    if not np.any(binary):
        raise ValueError("coverage mask cannot be entirely zero")

    return np.frombuffer(
        binary.tobytes(order="C"),
        dtype=np.uint8,
    ).reshape(binary.shape)


@dataclass(frozen=True, slots=True)
class ReferenceImage:
    """Detector-neutral decoded reference raster with stable identity."""

    key: str
    image: RasterImage
    coverage_mask: CoverageMask | None = field(
        default=None,
        compare=False,
        hash=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        if not isinstance(self.image, RasterImage):
            raise TypeError("reference image must be RasterImage")
        object.__setattr__(
            self,
            "image",
            materialize_image(self.image),
        )
        coverage_mask = None
        if self.coverage_mask is not None:
            coverage_mask = _freeze_coverage_mask(
                self.coverage_mask,
                expected_shape=(
                    self.image.height,
                    self.image.width,
                ),
            )

        object.__setattr__(
            self,
            "key",
            normalize_reference_asset_key(self.key),
        )
        object.__setattr__(
            self,
            "coverage_mask",
            coverage_mask,
        )

    @property
    def pixel_format(self) -> PixelFormat:
        return self.image.pixel_format

    @property
    def width(self) -> int:
        return self.image.width

    @property
    def height(self) -> int:
        return self.image.height

    @property
    def pixels(self) -> np.ndarray:
        return self.image.pixels
