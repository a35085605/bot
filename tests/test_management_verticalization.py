from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import get_type_hints
import unittest

from adb.management import (
    AdbTransportPreparation,
    AdbTransportPreparer,
)
from desktop_window.management import (
    WindowActivation,
    WindowActivator,
    WindowMove,
)
from execution.control import (
    ExecutionOperationResult,
    ExecutionOperationStatus,
    ScreenPoint as CompatibilityScreenPoint,
)
from execution.window import (
    WindowActivation as ExecutionWindowActivation,
    WindowActivator as ExecutionWindowActivator,
)
from management.adb import (
    AdbTransportPreparation as CompatibilityAdbTransportPreparation,
    AdbTransportPreparer as CompatibilityAdbTransportPreparer,
)
from management.window import (
    WindowActivation as CompatibilityWindowActivation,
    WindowActivator as CompatibilityWindowActivator,
)
from native_coordinates import ScreenPoint
from native_operation import NativeOperationResult, NativeOperationStatus
from observation.target_runtime import ControlChannelId


class ManagementVerticalizationTest(unittest.TestCase):
    def test_window_contracts_have_one_canonical_identity(self) -> None:
        self.assertIs(WindowActivation, CompatibilityWindowActivation)
        self.assertIs(WindowActivation, ExecutionWindowActivation)
        self.assertIs(WindowActivator, CompatibilityWindowActivator)
        self.assertIs(WindowActivator, ExecutionWindowActivator)
        self.assertEqual(
            WindowMove(" hwnd:42 ", ScreenPoint(-100, 20)).window_id,
            "hwnd:42",
        )

    def test_adb_contracts_have_one_canonical_identity(self) -> None:
        self.assertIs(
            AdbTransportPreparation,
            CompatibilityAdbTransportPreparation,
        )
        self.assertIs(
            AdbTransportPreparer,
            CompatibilityAdbTransportPreparer,
        )
        operation = AdbTransportPreparation(ControlChannelId(" adb:test "))
        self.assertEqual(operation.channel_id, ControlChannelId("adb:test"))

    def test_shared_native_values_keep_execution_compatibility(self) -> None:
        self.assertIs(ScreenPoint, CompatibilityScreenPoint)
        self.assertIs(NativeOperationResult, ExecutionOperationResult)
        self.assertIs(NativeOperationStatus, ExecutionOperationStatus)

        started = datetime(2026, 8, 6, tzinfo=timezone.utc)
        result = NativeOperationResult(
            status=NativeOperationStatus.SUCCEEDED,
            backend_id=" test ",
            started_at=started,
            finished_at=started + timedelta(milliseconds=1),
        )
        self.assertEqual(result.backend_id, "test")

    def test_management_ports_return_neutral_operation_results(self) -> None:
        self.assertIs(
            get_type_hints(WindowActivator.activate)["return"],
            NativeOperationResult,
        )
        self.assertIs(
            get_type_hints(AdbTransportPreparer.prepare)["return"],
            NativeOperationResult,
        )


if __name__ == "__main__":
    unittest.main()
