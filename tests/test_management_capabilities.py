from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import get_type_hints
import unittest

from adb.management import (
    AdbServerStart,
    AdbServerStop,
    AdbTransportPreparation,
    AdbTransportPreparer,
    AdbTransportRecovery,
)
from control_channel import ControlChannelId
from desktop_window.management import (
    WindowActivation,
    WindowActivator,
    WindowMove,
)
from native_coordinates import ScreenPoint
from native_operation import NativeOperationResult


class ManagementCapabilityDomainTest(unittest.TestCase):
    def test_window_management_requests_use_canonical_contracts(self) -> None:
        self.assertEqual(WindowActivation(" hwnd:42 ").window_id, "hwnd:42")
        self.assertEqual(
            WindowMove("hwnd:42", ScreenPoint(-100, 20)).top_left_screen,
            ScreenPoint(-100, 20),
        )

    def test_adb_server_requests_are_explicit_values(self) -> None:
        self.assertEqual(AdbServerStart(), AdbServerStart())
        self.assertEqual(AdbServerStop(), AdbServerStop())

    def test_adb_transport_requests_are_channel_aware_and_immutable(self) -> None:
        channel_id = ControlChannelId(" adb:emulator-5554 ")
        preparation = AdbTransportPreparation(channel_id)
        recovery = AdbTransportRecovery(channel_id)
        self.assertEqual(preparation.channel_id, ControlChannelId("adb:emulator-5554"))
        self.assertEqual(recovery.channel_id, preparation.channel_id)
        with self.assertRaises(FrozenInstanceError):
            preparation.channel_id = ControlChannelId("other")
        with self.assertRaises(TypeError):
            AdbTransportPreparation("adb")  # type: ignore[arg-type]

    def test_management_ports_return_native_operation_results(self) -> None:
        self.assertIs(get_type_hints(WindowActivator.activate)["return"], NativeOperationResult)
        self.assertIs(get_type_hints(AdbTransportPreparer.prepare)["return"], NativeOperationResult)


if __name__ == "__main__":
    unittest.main()
