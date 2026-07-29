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

    def view(self, bounds: Rect) -> RasterImageView:
        """Create a zero-copy rectangular view in image-local coordinates."""

        if not isinstance(bounds, Rect):
            raise TypeError("view bounds must be Rect")
        if not self.bounds.contains_rect(bounds):
            raise ValueError("view bounds must be contained by image bounds")
        return RasterImageView(root=self, bounds_in_root=bounds)


@dataclass(frozen=True, slots=True, eq=False)
class RasterImageView:
    """Immutable rectangular zero-copy view of one root ``RasterImage``.

    Every view stores its rectangle directly in root-raster coordinates.
    Creating a view from another view composes the local offset immediately,
    so no parent-view chain is retained. Resize, rotation, padding, arbitrary
    strides, and other non-translation mappings are intentionally not views.
    """

    root: RasterImage = field(compare=False, hash=False, repr=False)
    bounds_in_root: Rect
    _pixels: ImagePixels = field(
        init=False,
        compare=False,
        hash=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        if not isinstance(self.root, RasterImage):
            raise TypeError("view root must be RasterImage")
        if not isinstance(self.bounds_in_root, Rect):
            raise TypeError("bounds_in_root must be Rect")
        if not self.root.bounds.contains_rect(self.bounds_in_root):
            raise ValueError(
                "view bounds must be contained by root raster bounds"
            )

        pixels = _slice_pixels(
            self.root.pixels,
            bounds=self.bounds_in_root,
        )
        if not np.shares_memory(pixels, self.root.pixels):
            raise RuntimeError("view pixels must share memory with root raster")
        if pixels.flags.writeable:
            raise RuntimeError("view pixels must be read-only")

        object.__setattr__(self, "_pixels", pixels)

    @property
    def pixels(self) -> ImagePixels:
        return self._pixels

    @property
    def pixel_format(self) -> PixelFormat:
        return self.root.pixel_format

    @property
    def width(self) -> int:
        return self.bounds_in_root.width

    @property
    def height(self) -> int:
        return self.bounds_in_root.height

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

    def view(self, bounds: Rect) -> RasterImageView:
        """Create a child view and flatten it directly onto the root raster."""

        if not isinstance(bounds, Rect):
            raise TypeError("view bounds must be Rect")
        if not self.bounds.contains_rect(bounds):
            raise ValueError("view bounds must be contained by parent view")

        return RasterImageView(
            root=self.root,
            bounds_in_root=bounds.translated(
                dx=self.bounds_in_root.left,
                dy=self.bounds_in_root.top,
            ),
        )

    def local_rect_to_root(self, rect: Rect) -> Rect:
        if not isinstance(rect, Rect):
            raise TypeError("local rect must be Rect")
        if not self.bounds.contains_rect(rect):
            raise ValueError("local rect must be contained by view bounds")
        return rect.translated(
            dx=self.bounds_in_root.left,
            dy=self.bounds_in_root.top,
        )

    def root_rect_to_local(self, rect: Rect) -> Rect:
        if not isinstance(rect, Rect):
            raise TypeError("root rect must be Rect")
        if not self.bounds_in_root.contains_rect(rect):
            raise ValueError(
                "root rect must be contained by view bounds in root"
            )
        return rect.translated(
            dx=-self.bounds_in_root.left,
            dy=-self.bounds_in_root.top,
        )
