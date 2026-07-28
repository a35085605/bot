from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TypeAlias

import numpy as np
import numpy.typing as npt

from geometry.rect import Rect
from geometry.size import Size


ImagePixels: TypeAlias = npt.NDArray[np.uint8]


class Interpolation(str, Enum):
    NEAREST = "nearest"
    LINEAR = "linear"
    CUBIC = "cubic"
    AREA = "area"


@dataclass(frozen=True, slots=True)
class RasterImage:
    """Independently owned immutable uint8 raster."""

    pixels: ImagePixels = field(compare=False, hash=False, repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.pixels, np.ndarray):
            raise TypeError("raster pixels must be a numpy array")
        if self.pixels.dtype != np.uint8:
            raise TypeError(
                "raster pixels must be uint8, "
                f"got {self.pixels.dtype}"
            )
        if self.pixels.ndim not in (2, 3):
            raise ValueError(
                "raster pixels must be two- or three-dimensional, "
                f"got shape {self.pixels.shape}"
            )
        if any(dimension <= 0 for dimension in self.pixels.shape):
            raise ValueError("raster dimensions must be greater than zero")

        frozen = np.frombuffer(
            self.pixels.tobytes(order="C"),
            dtype=np.uint8,
        ).reshape(self.pixels.shape)
        object.__setattr__(self, "pixels", frozen)

    @property
    def width(self) -> int:
        return int(self.pixels.shape[1])

    @property
    def height(self) -> int:
        return int(self.pixels.shape[0])

    @property
    def channel_count(self) -> int:
        if self.pixels.ndim == 2:
            return 1
        return int(self.pixels.shape[2])

    @property
    def size(self) -> Size:
        return Size(width=self.width, height=self.height)

    @property
    def bounds(self) -> Rect:
        return Rect(x=0, y=0, width=self.width, height=self.height)
