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
    materialize_image,
)
from imaging.adapters import OpenCVImageResizer


class ImagingTest(unittest.TestCase):
    def test_imaging_exposes_one_public_raster_type(self) -> None:
        import imaging

        self.assertFalse(hasattr(imaging, "RasterImageView"))
        self.assertFalse(hasattr(imaging, "crop_image_view"))

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
        self.assertTrue(image.is_contiguous)
        self.assertTrue(image.is_materialized)
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

    def test_crop_returns_logical_raster_with_shared_storage(self) -> None:
        source = RasterImage(
            pixels=np.arange(6 * 8 * 3, dtype=np.uint8).reshape(6, 8, 3),
            pixel_format=PixelFormat.BGR24,
        )

        cropped = crop_image(
            source,
            bounds=Rect(x=2, y=1, width=4, height=3),
        )

        self.assertIsInstance(cropped, RasterImage)
        np.testing.assert_array_equal(
            cropped.pixels,
            source.pixels[1:4, 2:6, :],
        )
        self.assertTrue(np.shares_memory(cropped.pixels, source.pixels))
        self.assertEqual(cropped.bounds, Rect(x=0, y=0, width=4, height=3))
        self.assertEqual(cropped.size, Size(width=4, height=3))
        self.assertFalse(cropped.pixels.flags.writeable)
        self.assertFalse(cropped.is_contiguous)
        self.assertFalse(cropped.is_materialized)
        self.assertIs(cropped.pixel_format, PixelFormat.BGR24)

    def test_full_crop_reuses_same_logical_raster(self) -> None:
        image = RasterImage(
            pixels=np.arange(12, dtype=np.uint8).reshape(3, 4),
            pixel_format=PixelFormat.GRAY8,
        )

        self.assertIs(crop_image(image, bounds=image.bounds), image)

    def test_crop_rejects_bounds_outside_image(self) -> None:
        with self.assertRaises(ValueError):
            crop_image(
                RasterImage(
                    pixels=np.zeros((4, 5), dtype=np.uint8),
                    pixel_format=PixelFormat.GRAY8,
                ),
                bounds=Rect(x=4, y=3, width=2, height=2),
            )

    def test_nested_crop_flattens_directly_to_owned_backing(self) -> None:
        root = RasterImage(
            pixels=np.arange(10 * 12, dtype=np.uint8).reshape(10, 12),
            pixel_format=PixelFormat.GRAY8,
        )
        parent = crop_image(
            root,
            bounds=Rect(x=3, y=2, width=7, height=6),
        )

        child = crop_image(
            parent,
            bounds=Rect(x=2, y=1, width=3, height=4),
        )

        np.testing.assert_array_equal(child.pixels, root.pixels[3:7, 5:8])
        self.assertTrue(np.shares_memory(child.pixels, root.pixels))
        self.assertTrue(np.shares_memory(child.pixels, parent.pixels))

    def test_materialize_image_copies_crop_into_owned_raster(self) -> None:
        root = RasterImage(
            pixels=np.arange(5 * 7, dtype=np.uint8).reshape(5, 7),
            pixel_format=PixelFormat.GRAY8,
        )
        cropped = crop_image(
            root,
            bounds=Rect(x=1, y=1, width=4, height=3),
        )

        materialized = materialize_image(cropped)

        self.assertIsInstance(materialized, RasterImage)
        np.testing.assert_array_equal(materialized.pixels, cropped.pixels)
        self.assertFalse(np.shares_memory(materialized.pixels, root.pixels))
        self.assertFalse(materialized.pixels.flags.writeable)
        self.assertTrue(materialized.is_contiguous)
        self.assertTrue(materialized.is_materialized)

    def test_materialize_image_reuses_owned_raster(self) -> None:
        image = RasterImage(
            pixels=np.arange(12, dtype=np.uint8).reshape(3, 4),
            pixel_format=PixelFormat.GRAY8,
        )

        self.assertIs(materialize_image(image), image)

    def test_crop_accepts_logical_image_local_coordinates(self) -> None:
        root = RasterImage(
            pixels=np.arange(8 * 9, dtype=np.uint8).reshape(8, 9),
            pixel_format=PixelFormat.GRAY8,
        )
        parent = crop_image(
            root,
            bounds=Rect(x=2, y=1, width=5, height=6),
        )

        child = crop_image(
            parent,
            bounds=Rect(x=1, y=2, width=3, height=2),
        )

        np.testing.assert_array_equal(child.pixels, root.pixels[3:5, 3:6])
        self.assertTrue(np.shares_memory(child.pixels, root.pixels))

    def test_crop_rejects_bounds_outside_parent(self) -> None:
        root = RasterImage(
            pixels=np.zeros((5, 6), dtype=np.uint8),
            pixel_format=PixelFormat.GRAY8,
        )
        parent = crop_image(
            root,
            bounds=Rect(x=1, y=1, width=3, height=3),
        )

        with self.assertRaises(ValueError):
            crop_image(
                parent,
                bounds=Rect(x=2, y=2, width=2, height=2),
            )

    def test_opencv_resize_accepts_non_contiguous_logical_crop(self) -> None:
        root = RasterImage(
            pixels=np.arange(4 * 6, dtype=np.uint8).reshape(4, 6),
            pixel_format=PixelFormat.GRAY8,
        )
        cropped = crop_image(
            root,
            bounds=Rect(x=1, y=1, width=2, height=2),
        )
        self.assertFalse(cropped.is_contiguous)

        resized = OpenCVImageResizer().resize(
            cropped,
            target_size=Size(width=4, height=4),
            interpolation=Interpolation.NEAREST,
        )

        np.testing.assert_array_equal(
            resized.pixels,
            np.array(
                [
                    [7, 7, 8, 8],
                    [7, 7, 8, 8],
                    [13, 13, 14, 14],
                    [13, 13, 14, 14],
                ],
                dtype=np.uint8,
            ),
        )
        self.assertTrue(resized.is_contiguous)

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
