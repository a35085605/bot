from __future__ import annotations

import unittest

import numpy as np

from detector_input import FixedViewportRoiPreparer
from evidence import (
    EvidenceId,
    EvidenceKind,
    EvidenceProvenance,
)
from geometry.rect import Rect
from geometry.size import Size
from imaging import Interpolation, RasterImage
from imaging.adapters import OpenCVImageResizer
from observation import FrameId
from perception_integration import EvidenceAssembler


class DetectorInputPreparationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.preparer = FixedViewportRoiPreparer(
            resizer=OpenCVImageResizer()
        )
        self.image = RasterImage(
            pixels=np.arange(6 * 8, dtype=np.uint8).reshape(6, 8)
        )

    def test_prepares_fixed_roi_without_resize(self) -> None:
        prepared = self.preparer.prepare(
            frame_id=FrameId(7),
            source_id="game-window",
            root_bounds=Rect(x=0, y=0, width=8, height=6),
            image=self.image,
            roi_root=Rect(x=2, y=1, width=4, height=3),
            output_size=Size(width=4, height=3),
            interpolation=Interpolation.NEAREST,
        )

        np.testing.assert_array_equal(
            prepared.pixels,
            self.image.pixels[1:4, 2:6],
        )
        self.assertFalse(prepared.provenance.resized)
        self.assertEqual(
            prepared.context.roi_root,
            Rect(x=2, y=1, width=4, height=3),
        )

    def test_resize_records_detector_local_to_viewport_root_mapping(self) -> None:
        roi = Rect(x=2, y=1, width=4, height=3)
        prepared = self.preparer.prepare(
            frame_id=FrameId(7),
            source_id="game-window",
            root_bounds=Rect(x=0, y=0, width=8, height=6),
            image=self.image,
            roi_root=roi,
            output_size=Size(width=8, height=6),
            interpolation=Interpolation.NEAREST,
        )

        self.assertEqual(prepared.image.size, Size(width=8, height=6))
        self.assertTrue(prepared.provenance.resized)
        self.assertEqual(
            prepared.context.local_rect_to_root(
                Rect(x=0, y=0, width=8, height=6)
            ),
            roi,
        )
        self.assertEqual(
            prepared.context.local_rect_to_root(
                Rect(x=2, y=2, width=4, height=2)
            ),
            Rect(x=3, y=2, width=2, height=1),
        )

    def test_rejects_roi_outside_canonical_viewport(self) -> None:
        with self.assertRaises(ValueError):
            self.preparer.prepare(
                frame_id=FrameId(7),
                source_id="game-window",
                root_bounds=Rect(x=0, y=0, width=8, height=6),
                image=self.image,
                roi_root=Rect(x=7, y=5, width=2, height=2),
                output_size=Size(width=2, height=2),
            )

    def test_rejects_image_that_does_not_match_root_bounds(self) -> None:
        with self.assertRaises(ValueError):
            self.preparer.prepare(
                frame_id=FrameId(7),
                source_id="game-window",
                root_bounds=Rect(x=0, y=0, width=7, height=6),
                image=self.image,
                roi_root=Rect(x=1, y=1, width=2, height=2),
                output_size=Size(width=2, height=2),
            )

    def test_prepared_context_feeds_evidence_bridge(self) -> None:
        prepared = self.preparer.prepare(
            frame_id=FrameId(7),
            source_id="game-window",
            root_bounds=Rect(x=0, y=0, width=8, height=6),
            image=self.image,
            roi_root=Rect(x=2, y=1, width=4, height=3),
            output_size=Size(width=8, height=6),
            interpolation=Interpolation.NEAREST,
        )

        evidence = EvidenceAssembler.assemble(
            context=prepared.context,
            evidence_id=EvidenceId("login-button"),
            kind=EvidenceKind("template.match"),
            score=0.95,
            provenance=EvidenceProvenance(
                detector_id="opencv.template",
                asset_keys=("template.login_button_active",),
            ),
            result={"matched": True},
            bounds_local=Rect(x=2, y=2, width=4, height=2),
        )

        self.assertEqual(
            evidence.roi_root,
            Rect(x=2, y=1, width=4, height=3),
        )
        self.assertEqual(
            evidence.bounds_root,
            Rect(x=3, y=2, width=2, height=1),
        )


if __name__ == "__main__":
    unittest.main()
