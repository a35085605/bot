from __future__ import annotations

import unittest

import execution
import geometry
import observation
from execution import ContentPointTarget, ExecutionTargetResolver
from execution.input import PointerClick
from execution.lifecycle import TargetLaunch
from geometry import Point, Rect, RelativePoint, Size
from observation import ObservationBundle, ObservationCoherence
from observation.capture import FrameId
from observation.target_runtime import TargetRuntimeSnapshot


class PublicNamespaceTest(unittest.TestCase):
    def test_observation_root_only_exports_cross_family_grouping(self) -> None:
        self.assertEqual(
            set(observation.__all__),
            {"ObservationBundle", "ObservationCoherence"},
        )
        self.assertIs(observation.ObservationBundle, ObservationBundle)
        self.assertIs(observation.ObservationCoherence, ObservationCoherence)
        self.assertFalse(hasattr(observation, "FrameId"))
        self.assertFalse(hasattr(observation, "TargetRuntimeSnapshot"))
        self.assertEqual(FrameId.__module__, "observation.capture.domain.models")
        self.assertEqual(
            TargetRuntimeSnapshot.__module__,
            "observation.target_runtime.domain.snapshots",
        )

    def test_execution_root_only_exports_target_resolution(self) -> None:
        self.assertEqual(
            set(execution.__all__),
            {
                "ContentPointTarget",
                "ContentRectTarget",
                "ExecutionTargetFailureReason",
                "ExecutionTargetResolution",
                "ExecutionTargetResolver",
                "ExecutionTargetUnavailable",
                "ResolvedExecutionTarget",
            },
        )
        self.assertIs(execution.ContentPointTarget, ContentPointTarget)
        self.assertIs(execution.ExecutionTargetResolver, ExecutionTargetResolver)
        self.assertFalse(hasattr(execution, "PointerClick"))
        self.assertFalse(hasattr(execution, "TargetLaunch"))
        self.assertEqual(PointerClick.__module__, "execution.input.domain")
        self.assertEqual(TargetLaunch.__module__, "execution.lifecycle.domain")

    def test_geometry_root_exports_stable_primitives(self) -> None:
        self.assertEqual(
            set(geometry.__all__),
            {"Point", "Rect", "RelativePoint", "Size"},
        )
        self.assertIs(geometry.Point, Point)
        self.assertIs(geometry.Rect, Rect)
        self.assertIs(geometry.RelativePoint, RelativePoint)
        self.assertIs(geometry.Size, Size)


if __name__ == "__main__":
    unittest.main()
