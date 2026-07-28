from __future__ import annotations

import unittest

import numpy as np

from geometry.rect import Rect
from geometry.size import Size
from imaging import Interpolation, RasterImage, crop_image
from imaging.adapters import OpenCVImageResizer


class ImagingTest(unittest.TestCase):
    def test_raster_owns_immutable_pixels(self) -> None:
        source = np.arange(12, dtype=np.uint8).reshape(3, 4)
        image = RasterImage(pixels=source)

        source[:, :] = 0

        np.testing.assert_array_equal(
            image.pixels,
            np.arange(12, dtype=np.uint8).reshape(3, 4),
        )
        self.assertFalse(image.pixels.flags.writeable)
        self.assertEqual(image.size, Size(width=4, height=3))

    def test_crop_is_general_and_independently_owned(self) -> None:
        source = RasterImage(
            pixels=np.arange(6 * 8 * 3, dtype=np.uint8).reshape(6, 8, 3)
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

    def test_crop_rejects_bounds_outside_image(self) -> None:
        with self.assertRaises(ValueError):
            crop_image(
                RasterImage(pixels=np.zeros((4, 5), dtype=np.uint8)),
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
            )
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


if __name__ == "__main__":
    unittest.main()
