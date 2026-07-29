from __future__ import annotations

import unittest

import numpy as np

from geometry.rect import Rect
from geometry.size import Size
from imaging import (
    Interpolation,
    PixelFormat,
    RasterImage,
    crop_image,
)
from imaging.adapters import OpenCVImageResizer


class ImagingTest(unittest.TestCase):
    def test_raster_owns_immutable_pixels_and_format(self) -> None:
        source = np.arange(12, dtype=np.uint8).reshape(3, 4)
        image = RasterImage(
            pixels=source,
            pixel_format=PixelFormat.GRAY8,
        )

        source[:, :] = 0

        np.testing.assert_array_equal(
            image.pixels,
            np.arange(12, dtype=np.uint8).reshape(3, 4),
        )
        self.assertFalse(image.pixels.flags.writeable)
        self.assertEqual(image.size, Size(width=4, height=3))
        self.assertEqual(image.dtype, np.dtype(np.uint8))
        self.assertEqual(image.channel_count, 1)
        self.assertIs(image.pixel_format, PixelFormat.GRAY8)

    def test_raster_validates_dtype_dimensions_and_channels(self) -> None:
        with self.subTest("dtype"):
            with self.assertRaises(TypeError):
                RasterImage(
                    pixels=np.zeros((3, 4), dtype=np.float32),
                    pixel_format=PixelFormat.GRAY8,
                )

        with self.subTest("gray dimensions"):
            with self.assertRaises(ValueError):
                RasterImage(
                    pixels=np.zeros((3, 4, 1), dtype=np.uint8),
                    pixel_format=PixelFormat.GRAY8,
                )

        with self.subTest("color channels"):
            with self.assertRaises(ValueError):
                RasterImage(
                    pixels=np.zeros((3, 4, 3), dtype=np.uint8),
                    pixel_format=PixelFormat.BGRA32,
                )

    def test_crop_is_general_and_independently_owned(self) -> None:
        source = RasterImage(
            pixels=np.arange(6 * 8 * 3, dtype=np.uint8).reshape(6, 8, 3),
            pixel_format=PixelFormat.BGR24,
        )

        cropped = crop_image(
            source,
            bounds=Rect(x=2, y=1, width=4, height=3),
        )

        np.testing.assert_array_equal(
            cropped.pixels,
            source.pixels[1:4, 2:6, :],
        )
        self.assertEqual(cropped.size, Size(width=4, height=3))
        self.assertFalse(cropped.pixels.flags.writeable)
        self.assertIs(cropped.pixel_format, PixelFormat.BGR24)

    def test_crop_rejects_bounds_outside_image(self) -> None:
        with self.assertRaises(ValueError):
            crop_image(
                RasterImage(
                    pixels=np.zeros((4, 5), dtype=np.uint8),
                    pixel_format=PixelFormat.GRAY8,
                ),
                bounds=Rect(x=4, y=3, width=2, height=2),
            )

    def test_opencv_nearest_resize_is_deterministic(self) -> None:
        image = RasterImage(
            pixels=np.array(
                [
                    [1, 2],
                    [3, 4],
                ],
                dtype=np.uint8,
            ),
            pixel_format=PixelFormat.GRAY8,
        )

        resized = OpenCVImageResizer().resize(
            image,
            target_size=Size(width=4, height=4),
            interpolation=Interpolation.NEAREST,
        )

        np.testing.assert_array_equal(
            resized.pixels,
            np.array(
                [
                    [1, 1, 2, 2],
                    [1, 1, 2, 2],
                    [3, 3, 4, 4],
                    [3, 3, 4, 4],
                ],
                dtype=np.uint8,
            ),
        )
        self.assertIs(resized.pixel_format, PixelFormat.GRAY8)


if __name__ == "__main__":
    unittest.main()
