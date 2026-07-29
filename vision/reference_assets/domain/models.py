from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import numpy as np
import numpy.typing as npt

from imaging import RasterImage
from vision.reference_assets.domain.keys import (
    normalize_reference_asset_key,
)


CoverageMask = npt.NDArray[np.uint8]


class ReferenceImageFormat(str, Enum):
    GRAY8 = "gray8"
    BGR24 = "bgr24"
    BGRA32 = "bgra32"

    @property
    def channel_count(self) -> int:
        if self is ReferenceImageFormat.GRAY8:
            return 1
        if self is ReferenceImageFormat.BGR24:
            return 3
        return 4


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
    pixel_format: ReferenceImageFormat
    coverage_mask: CoverageMask | None = field(
        default=None,
        compare=False,
        hash=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        if not isinstance(self.image, RasterImage):
            raise TypeError("reference image must be RasterImage")
        if not isinstance(self.pixel_format, ReferenceImageFormat):
            raise TypeError(
                "pixel_format must be ReferenceImageFormat"
            )
        if self.image.channel_count != self.pixel_format.channel_count:
            raise ValueError(
                "reference image channel count must match pixel format"
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
    def width(self) -> int:
        return self.image.width

    @property
    def height(self) -> int:
        return self.image.height

    @property
    def pixels(self) -> np.ndarray:
        return self.image.pixels
