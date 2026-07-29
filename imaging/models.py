from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TypeAlias

import numpy as np
import numpy.typing as npt

from geometry.rect import Rect
from geometry.size import Size


ImagePixels: TypeAlias = npt.NDArray[np.uint8]


class PixelFormat(str, Enum):
    """Storage format required to interpret one raster's pixels."""

    GRAY8 = "gray8"
    BGR24 = "bgr24"
    BGRA32 = "bgra32"

    @property
    def dtype(self) -> np.dtype:
        return np.dtype(np.uint8)

    @property
    def channel_count(self) -> int:
        if self is PixelFormat.GRAY8:
            return 1
        if self is PixelFormat.BGR24:
            return 3
        return 4

    @property
    def dimension_count(self) -> int:
        return 2 if self.channel_count == 1 else 3


class Interpolation(str, Enum):
    NEAREST = "nearest"
    LINEAR = "linear"
    CUBIC = "cubic"
    AREA = "area"


def _slice_pixels(
    pixels: ImagePixels,
    *,
    bounds: Rect,
) -> ImagePixels:
    if pixels.ndim == 2:
        return pixels[
            bounds.top:bounds.bottom,
            bounds.left:bounds.right,
        ]
    return pixels[
        bounds.top:bounds.bottom,
        bounds.left:bounds.right,
        :,
    ]


@dataclass(frozen=True, slots=True)
class RasterImage:
    """Independently owned immutable raster with explicit pixel format."""

    pixels: ImagePixels = field(compare=False, hash=False, repr=False)
    pixel_format: PixelFormat

    def __post_init__(self) -> None:
        if not isinstance(self.pixels, np.ndarray):
            raise TypeError("raster pixels must be a numpy array")
        if not isinstance(self.pixel_format, PixelFormat):
            raise TypeError("pixel_format must be PixelFormat")
        if self.pixels.dtype != self.pixel_format.dtype:
            raise TypeError(
                "raster pixel dtype must match pixel format: "
                f"expected {self.pixel_format.dtype}, "
                f"got {self.pixels.dtype}"
            )
        if self.pixels.ndim != self.pixel_format.dimension_count:
            raise ValueError(
                "raster pixel dimensions must match pixel format: "
                f"expected {self.pixel_format.dimension_count}D, "
                f"got shape {self.pixels.shape}"
            )
        if self.pixels.shape[0] <= 0 or self.pixels.shape[1] <= 0:
            raise ValueError("raster width and height must be greater than zero")
        if (
            self.pixel_format.dimension_count == 3
            and self.pixels.shape[2] != self.pixel_format.channel_count
        ):
            raise ValueError(
                "raster channel count must match pixel format: "
                f"expected {self.pixel_format.channel_count}, "
                f"got {self.pixels.shape[2]}"
            )

        frozen = np.frombuffer(
            self.pixels.tobytes(order="C"),
            dtype=self.pixel_format.dtype,
        ).reshape(self.pixels.shape)
        object.__setattr__(self, "pixels", frozen)

    @property
    def width(self) -> int:
        return int(self.pixels.shape[1])

    @property
    def height(self) -> int:
        return int(self.pixels.shape[0])

    @property
    def dtype(self) -> np.dtype:
        return self.pixels.dtype

    @property
    def channel_count(self) -> int:
        return self.pixel_format.channel_count

    @property
    def size(self) -> Size:
        return Size(width=self.width, height=self.height)

    @property
    def bounds(self) -> Rect:
        return Rect(x=0, y=0, width=self.width, height=self.height)


@dataclass(frozen=True, slots=True, init=False, eq=False)
class RasterImageView:
    """Read-only borrowed raster backed by one owned ``RasterImage``.

    Backing placement exists only to retain the owned raster and compose nested
    zero-copy crops. Consumers observe a local raster whose bounds begin at
    ``(0, 0)``; coordinate-space placement belongs to higher-level models.
    """

    _backing_image: RasterImage = field(
        compare=False,
        hash=False,
        repr=False,
    )
    _bounds_in_backing: Rect = field(
        compare=False,
        hash=False,
        repr=False,
    )
    _pixels: ImagePixels = field(
        compare=False,
        hash=False,
        repr=False,
    )

    def __init__(self) -> None:
        raise TypeError(
            "RasterImageView cannot be constructed directly; "
            "use crop_image_view()"
        )

    @classmethod
    def _from_backing(
        cls,
        *,
        backing_image: RasterImage,
        bounds_in_backing: Rect,
    ) -> RasterImageView:
        if not isinstance(backing_image, RasterImage):
            raise TypeError("backing_image must be RasterImage")
        if not isinstance(bounds_in_backing, Rect):
            raise TypeError("bounds_in_backing must be Rect")
        if not backing_image.bounds.contains_rect(bounds_in_backing):
            raise ValueError(
                "view bounds must be contained by backing image bounds"
            )

        pixels = _slice_pixels(
            backing_image.pixels,
            bounds=bounds_in_backing,
        )
        if not np.shares_memory(pixels, backing_image.pixels):
            raise RuntimeError(
                "view pixels must share memory with backing image"
            )
        if pixels.flags.writeable:
            raise RuntimeError("view pixels must be read-only")

        instance = object.__new__(cls)
        object.__setattr__(instance, "_backing_image", backing_image)
        object.__setattr__(
            instance,
            "_bounds_in_backing",
            bounds_in_backing,
        )
        object.__setattr__(instance, "_pixels", pixels)
        return instance

    @property
    def pixels(self) -> ImagePixels:
        return self._pixels

    @property
    def pixel_format(self) -> PixelFormat:
        return self._backing_image.pixel_format

    @property
    def width(self) -> int:
        return int(self.pixels.shape[1])

    @property
    def height(self) -> int:
        return int(self.pixels.shape[0])

    @property
    def dtype(self) -> np.dtype:
        return self.pixels.dtype

    @property
    def channel_count(self) -> int:
        return self.pixel_format.channel_count

    @property
    def size(self) -> Size:
        return Size(width=self.width, height=self.height)

    @property
    def bounds(self) -> Rect:
        """View-local bounds beginning at ``(0, 0)``."""

        return Rect(x=0, y=0, width=self.width, height=self.height)

    @property
    def is_contiguous(self) -> bool:
        return bool(self.pixels.flags.c_contiguous)
