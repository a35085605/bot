from __future__ import annotations

from dataclasses import FrozenInstanceError
import unittest

from execution import ScreenPoint
from execution.window import (
    WindowActivator as CompatibilityWindowActivator,
)
from management.adb import (
    AdbServerStart,
    AdbServerStop,
    AdbTransportPreparation,
    AdbTransportRecovery,
)
from management.window import (
    WindowActivation,
    WindowActivator,
    WindowMove,
)
from observation.target_runtime import ControlChannelId


class ManagementCapabilityDomainTest(unittest.TestCase):
    def test_window_management_ports_keep_execution_compatibility(self) -> None:
        self.assertIs(WindowActivator, CompatibilityWindowActivator)
        self.assertEqual(
            WindowActivation(" hwnd:42 ").window_id,
            "hwnd:42",
        )
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

        self.assertEqual(
            preparation.channel_id,
            ControlChannelId("adb:emulator-5554"),
        )
        self.assertEqual(recovery.channel_id, preparation.channel_id)

        with self.assertRaises(FrozenInstanceError):
            preparation.channel_id = ControlChannelId("other")
        with self.assertRaises(TypeError):
            AdbTransportPreparation("adb")  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
