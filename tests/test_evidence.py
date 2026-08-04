from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import timedelta
import unittest

from evidence import (
    Evidence,
    EvidenceId,
    EvidenceKind,
    EvidenceProvenance,
    EvidenceSet,
)
from geometry.rect import Rect
from observation import FrameId


class EvidenceTest(unittest.TestCase):
    def _evidence(
        self,
        evidence_id: str,
        *,
        score: float = 0.9,
        frame_id: int = 7,
        source_id: str = "game-window",
        kind: str = "template.match",
        detector_id: str = "opencv.template",
        roi_root: Rect | None = None,
        bounds_root: Rect | None = None,
        result: object = "submit",
    ) -> Evidence[object]:
        roi = roi_root or Rect(
            x=100,
            y=200,
            width=400,
            height=300,
        )
        return Evidence(
            evidence_id=EvidenceId(evidence_id),
            frame_id=FrameId(frame_id),
            source_id=source_id,
            kind=EvidenceKind(kind),
            score=score,
            roi_root=roi,
            bounds_root=bounds_root,
            provenance=EvidenceProvenance(
                detector_id=detector_id,
                detector_version="1.2.0",
                parameter_digest="sha256:abc",
                asset_keys=("ui.submit",),
            ),
            result=result,
            duration=timedelta(milliseconds=4),
        )

    def test_normalizes_identity_and_provenance_text(self) -> None:
        evidence = Evidence(
            evidence_id=EvidenceId(" match-1 "),
            frame_id=FrameId(1),
            source_id=" game-window ",
            kind=EvidenceKind(" template.match "),
            score=0.75,
            roi_root=Rect(x=0, y=0, width=100, height=100),
            provenance=EvidenceProvenance(
                detector_id=" opencv.template ",
                detector_version=" 1.0 ",
                asset_keys=(" submit ",),
            ),
            result="submit",
        )

        self.assertEqual(evidence.evidence_id.value, "match-1")
        self.assertEqual(evidence.source_id, "game-window")
        self.assertEqual(evidence.kind.value, "template.match")
        self.assertEqual(
            evidence.provenance.detector_id,
            "opencv.template",
        )
        self.assertEqual(evidence.provenance.asset_keys, ("submit",))

    def test_evidence_is_immutable_and_accepts_typed_results(self) -> None:
        result = ("submit", Rect(x=120, y=220, width=40, height=20))
        evidence = self._evidence("match-1", result=result)

        self.assertIs(evidence.result, result)
        with self.assertRaises(FrozenInstanceError):
            evidence.score = 0.2

    def test_rejects_invalid_score(self) -> None:
        with self.assertRaises(ValueError):
            self._evidence("match-1", score=1.1)

    def test_bounds_must_be_inside_detector_roi(self) -> None:
        with self.assertRaises(ValueError):
            self._evidence(
                "match-1",
                roi_root=Rect(x=100, y=100, width=100, height=100),
                bounds_root=Rect(x=50, y=50, width=20, height=20),
            )

    def test_provenance_rejects_duplicate_asset_keys(self) -> None:
        with self.assertRaises(ValueError):
            EvidenceProvenance(
                detector_id="opencv.template",
                asset_keys=("submit", "submit"),
            )

    def test_set_owns_a_tuple_for_exactly_one_frame(self) -> None:
        first = self._evidence("match-1")
        second = self._evidence(
            "ocr-1",
            score=0.8,
            kind="ocr.text",
            detector_id="tesseract.ocr",
            result="42",
        )
        evidence_set = EvidenceSet(
            frame_id=FrameId(7),
            source_id="game-window",
            root_bounds=Rect(x=0, y=0, width=1920, height=1080),
            items=(first, second),
        )

        self.assertEqual(len(evidence_set), 2)
        self.assertEqual(tuple(evidence_set), (first, second))
        self.assertIs(
            evidence_set.get(EvidenceId("match-1")),
            first,
        )

    def test_set_rejects_duplicate_ids(self) -> None:
        first = self._evidence("match-1")
        duplicate = self._evidence(
            "match-1",
            result="cancel",
        )

        with self.assertRaises(ValueError):
            EvidenceSet(
                frame_id=FrameId(7),
                source_id="game-window",
                root_bounds=Rect(
                    x=0,
                    y=0,
                    width=1920,
                    height=1080,
                ),
                items=(first, duplicate),
            )

    def test_set_rejects_mixed_frames_and_sources(self) -> None:
        with self.assertRaises(ValueError):
            EvidenceSet(
                frame_id=FrameId(7),
                source_id="game-window",
                root_bounds=Rect(
                    x=0,
                    y=0,
                    width=1920,
                    height=1080,
                ),
                items=(self._evidence("match-1", frame_id=8),),
            )

        with self.assertRaises(ValueError):
            EvidenceSet(
                frame_id=FrameId(7),
                source_id="game-window",
                root_bounds=Rect(
                    x=0,
                    y=0,
                    width=1920,
                    height=1080,
                ),
                items=(
                    self._evidence(
                        "match-1",
                        source_id="other-window",
                    ),
                ),
            )

    def test_set_rejects_roi_outside_frame_root(self) -> None:
        with self.assertRaises(ValueError):
            EvidenceSet(
                frame_id=FrameId(7),
                source_id="game-window",
                root_bounds=Rect(x=0, y=0, width=200, height=200),
                items=(
                    self._evidence(
                        "match-1",
                        roi_root=Rect(
                            x=100,
                            y=100,
                            width=200,
                            height=200,
                        ),
                    ),
                ),
            )

    def test_set_queries_preserve_order_and_find_best_score(self) -> None:
        template_low = self._evidence("template-low", score=0.7)
        ocr = self._evidence(
            "ocr",
            score=0.95,
            kind="ocr.text",
            detector_id="tesseract.ocr",
        )
        template_high = self._evidence(
            "template-high",
            score=0.9,
        )
        evidence_set = EvidenceSet(
            frame_id=FrameId(7),
            source_id="game-window",
            root_bounds=Rect(x=0, y=0, width=1920, height=1080),
            items=(template_low, ocr, template_high),
        )

        self.assertEqual(
            evidence_set.of_kind(EvidenceKind("template.match")),
            (template_low, template_high),
        )
        self.assertEqual(
            evidence_set.from_detector("opencv.template"),
            (template_low, template_high),
        )
        self.assertIs(evidence_set.best(), ocr)
        self.assertIs(
            evidence_set.best(kind=EvidenceKind("template.match")),
            template_high,
        )


if __name__ == "__main__":
    unittest.main()
