import unittest

from capture import CapturedFrame as LegacyCapturedFrame
from capture.domain.models import FrameId as LegacyFrameId
from observation.capture import CapturedFrame, FrameId
from observation.target_runtime import TargetId, TargetRuntimeSnapshot
from observation.temporal import TemporalSnapshot
from target_runtime import TargetId as LegacyTargetId
from target_runtime import TargetRuntimeSnapshot as LegacyTargetRuntimeSnapshot
from temporal import TemporalSnapshot as LegacyTemporalSnapshot


class ObservationNamespaceTests(unittest.TestCase):
    def test_capture_legacy_exports_preserve_identity(self) -> None:
        self.assertIs(LegacyCapturedFrame, CapturedFrame)
        self.assertIs(LegacyFrameId, FrameId)

    def test_target_runtime_legacy_exports_preserve_identity(self) -> None:
        self.assertIs(LegacyTargetId, TargetId)
        self.assertIs(LegacyTargetRuntimeSnapshot, TargetRuntimeSnapshot)

    def test_temporal_legacy_exports_preserve_identity(self) -> None:
        self.assertIs(LegacyTemporalSnapshot, TemporalSnapshot)


if __name__ == "__main__":
    unittest.main()
