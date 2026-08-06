from __future__ import annotations

from datetime import timedelta
import unittest

from detector_input import DetectorInputContext, ImagePlacement
from evidence import (
    EvidenceAssembler,
    EvidenceId,
    EvidenceKind,
    EvidenceProvenance,
)
from geometry.rect import Rect
from observation.capture import FrameId


class EvidenceBridgeTest(unittest.TestCase):
    def _context(
        self,
        *,
        source_bounds_root: Rect | None = None,
        input_bounds_local: Rect | None = None,
        content_bounds_local: Rect | None = None,
    ) -> DetectorInputContext:
        source = source_bounds_root or Rect(
            x=300,
            y=200,
            width=400,
            height=300,
        )
        input_bounds = input_bounds_local or Rect(
            x=0,
            y=0,
            width=400,
            height=300,
        )
        content_bounds = content_bounds_local or input_bounds

        return DetectorInputContext(
            frame_id=FrameId(7),
            source_id=" game-window ",
            root_bounds=Rect(x=0, y=0, width=1920, height=1080),
            placement=ImagePlacement(
                input_bounds_local=input_bounds,
                content_bounds_local=content_bounds,
                source_bounds_root=source,
            ),
        )

    def test_context_normalizes_source_and_maps_unscaled_crop(self) -> None:
        context = self._context()

        self.assertEqual(context.source_id, "game-window")
        self.assertEqual(
            context.local_rect_to_root(
                Rect(x=20, y=10, width=40, height=20)
            ),
            Rect(x=320, y=210, width=40, height=20),
        )

    def test_mapping_contains_complete_result_after_resize(self) -> None:
        context = self._context(
            source_bounds_root=Rect(x=100, y=200, width=100, height=50),
            input_bounds_local=Rect(x=0, y=0, width=40, height=20),
        )

        self.assertEqual(
            context.local_rect_to_root(
                Rect(x=1, y=1, width=3, height=2)
            ),
            Rect(x=102, y=202, width=8, height=6),
        )

    def test_mapping_ignores_detector_letterbox_padding(self) -> None:
        context = self._context(
            source_bounds_root=Rect(x=100, y=200, width=100, height=50),
            input_bounds_local=Rect(x=0, y=0, width=40, height=40),
            content_bounds_local=Rect(x=0, y=10, width=40, height=20),
        )

        self.assertEqual(
            context.local_rect_to_root(
                Rect(x=4, y=12, width=8, height=4)
            ),
            Rect(x=110, y=205, width=20, height=10),
        )

    def test_rejects_invalid_spatial_contract(self) -> None:
        with self.assertRaises(ValueError):
            DetectorInputContext(
                frame_id=FrameId(1),
                source_id="game-window",
                root_bounds=Rect(x=0, y=0, width=100, height=100),
                placement=ImagePlacement(
                    input_bounds_local=Rect(
                        x=0,
                        y=0,
                        width=20,
                        height=20,
                    ),
                    content_bounds_local=Rect(
                        x=0,
                        y=0,
                        width=20,
                        height=20,
                    ),
                    source_bounds_root=Rect(
                        x=90,
                        y=90,
                        width=20,
                        height=20,
                    ),
                ),
            )

        with self.assertRaises(ValueError):
            ImagePlacement(
                input_bounds_local=Rect(
                    x=1,
                    y=0,
                    width=400,
                    height=300,
                ),
                content_bounds_local=Rect(
                    x=1,
                    y=0,
                    width=400,
                    height=300,
                ),
                source_bounds_root=Rect(
                    x=0,
                    y=0,
                    width=400,
                    height=300,
                ),
            )

        with self.assertRaises(ValueError):
            ImagePlacement(
                input_bounds_local=Rect(
                    x=0,
                    y=0,
                    width=40,
                    height=40,
                ),
                content_bounds_local=Rect(
                    x=0,
                    y=10,
                    width=40,
                    height=40,
                ),
                source_bounds_root=Rect(
                    x=0,
                    y=0,
                    width=100,
                    height=100,
                ),
            )

    def test_rejects_bounds_in_detector_padding(self) -> None:
        context = self._context(
            source_bounds_root=Rect(x=100, y=200, width=100, height=50),
            input_bounds_local=Rect(x=0, y=0, width=40, height=40),
            content_bounds_local=Rect(x=0, y=10, width=40, height=20),
        )

        with self.assertRaises(ValueError):
            context.local_rect_to_root(
                Rect(x=4, y=2, width=8, height=4)
            )

    def test_assembles_contextualized_evidence(self) -> None:
        context = self._context()
        detector_result = {"template_key": "ui.submit"}
        provenance = EvidenceProvenance(
            detector_id="opencv.template",
            detector_version="1.0",
            asset_keys=("ui.submit",),
        )

        evidence = EvidenceAssembler.assemble(
            context=context,
            evidence_id=EvidenceId("template-1"),
            kind=EvidenceKind("template.match"),
            score=0.93,
            provenance=provenance,
            result=detector_result,
            bounds_local=Rect(x=20, y=10, width=40, height=20),
            duration=timedelta(milliseconds=4),
        )

        self.assertEqual(evidence.frame_id, FrameId(7))
        self.assertEqual(evidence.source_id, "game-window")
        self.assertEqual(
            evidence.roi_root,
            Rect(x=300, y=200, width=400, height=300),
        )
        self.assertEqual(
            evidence.bounds_root,
            Rect(x=320, y=210, width=40, height=20),
        )
        self.assertIs(evidence.result, detector_result)
        self.assertIs(evidence.provenance, provenance)

    def test_assembles_non_localized_evidence(self) -> None:
        evidence = EvidenceAssembler.assemble(
            context=self._context(),
            evidence_id=EvidenceId("hash-1"),
            kind=EvidenceKind("hash.similarity"),
            score=0.8,
            provenance=EvidenceProvenance(
                detector_id="perceptual.hash"
            ),
            result="inventory-screen",
        )

        self.assertIsNone(evidence.bounds_root)


if __name__ == "__main__":
    unittest.main()
