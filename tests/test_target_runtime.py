from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
import unittest

from target_runtime import (
    AdbChannelInspector,
    AdbChannelState,
    AdbDeviceStatus,
    ControlCapability,
    ControlChannelId,
    ControlChannelKind,
    ControlChannelSnapshot,
    ControlChannelStatus,
    FocusStatus,
    ReadinessBlocker,
    TargetAvailability,
    TargetId,
    TargetRuntimeSnapshot,
    WindowChannelInspector,
    WindowChannelState,
)


class StaticWindowChannelInspector:
    def __init__(
        self,
        snapshot: ControlChannelSnapshot[WindowChannelState],
    ) -> None:
        self._snapshot = snapshot

    def inspect(
        self,
        target_id: TargetId,
    ) -> ControlChannelSnapshot[WindowChannelState]:
        if not isinstance(target_id, TargetId):
            raise TypeError("target_id must be TargetId")
        return self._snapshot


class StaticAdbChannelInspector:
    def __init__(
        self,
        snapshot: ControlChannelSnapshot[AdbChannelState],
    ) -> None:
        self._snapshot = snapshot

    def inspect(
        self,
        target_id: TargetId,
    ) -> ControlChannelSnapshot[AdbChannelState]:
        if not isinstance(target_id, TargetId):
            raise TypeError("target_id must be TargetId")
        return self._snapshot


class TargetRuntimeTest(unittest.TestCase):
    def _window_channel(
        self,
    ) -> ControlChannelSnapshot[WindowChannelState]:
        return ControlChannelSnapshot(
            channel_id=ControlChannelId(" desktop "),
            kind=ControlChannelKind.DESKTOP_WINDOW,
            status=ControlChannelStatus.READY,
            capabilities=frozenset(
                {
                    ControlCapability.POINTER,
                    ControlCapability.KEYBOARD,
                    ControlCapability.TEXT,
                }
            ),
            details=WindowChannelState(
                window_id=" hwnd:42 ",
                foreground_window_id=" hwnd:42 ",
                focus=FocusStatus.TARGET,
                minimized=False,
                visible=True,
                responsive=True,
            ),
        )

    def _adb_channel(
        self,
    ) -> ControlChannelSnapshot[AdbChannelState]:
        return ControlChannelSnapshot(
            channel_id=ControlChannelId("adb:emulator-5554"),
            kind=ControlChannelKind.ADB,
            status=ControlChannelStatus.BLOCKED,
            capabilities=frozenset(
                {
                    ControlCapability.POINTER,
                    ControlCapability.KEYBOARD,
                    ControlCapability.BACK,
                }
            ),
            blockers=(ReadinessBlocker("adb.unauthorized"),),
            details=AdbChannelState(
                serial=" emulator-5554 ",
                server_reachable=True,
                device_status=AdbDeviceStatus.UNAUTHORIZED,
                transport_ready=False,
            ),
        )

    def test_runtime_snapshot_normalizes_identity_and_queries_channels(
        self,
    ) -> None:
        window = self._window_channel()
        adb = self._adb_channel()
        snapshot = TargetRuntimeSnapshot(
            target_id=TargetId(" emulator "),
            observed_at=datetime(2026, 7, 28, tzinfo=timezone.utc),
            availability=TargetAvailability.AVAILABLE,
            inspector_id=" combined-runtime ",
            channels=(window, adb),
        )

        self.assertEqual(snapshot.target_id.value, "emulator")
        self.assertEqual(snapshot.inspector_id, "combined-runtime")
        self.assertEqual(window.channel_id.value, "desktop")
        self.assertEqual(window.details.window_id, "hwnd:42")
        self.assertEqual(adb.details.serial, "emulator-5554")
        self.assertEqual(
            snapshot.channel(ControlChannelId("desktop")),
            window,
        )
        self.assertEqual(snapshot.ready_channels, (window,))
        self.assertTrue(snapshot.supports(ControlCapability.POINTER))
        self.assertTrue(snapshot.supports(ControlCapability.TEXT))
        self.assertFalse(snapshot.supports(ControlCapability.BACK))

    def test_per_channel_inspectors_compose_runtime_channels(self) -> None:
        target_id = TargetId("emulator")
        window_inspector: WindowChannelInspector = (
            StaticWindowChannelInspector(self._window_channel())
        )
        adb_inspector: AdbChannelInspector = StaticAdbChannelInspector(
            self._adb_channel()
        )

        channels = (
            window_inspector.inspect(target_id),
            adb_inspector.inspect(target_id),
        )
        snapshot = TargetRuntimeSnapshot(
            target_id=target_id,
            observed_at=datetime(2026, 7, 31, tzinfo=timezone.utc),
            availability=TargetAvailability.AVAILABLE,
            inspector_id="composite",
            channels=channels,
        )

        self.assertIsInstance(
            snapshot.channels[0].details,
            WindowChannelState,
        )
        self.assertIsInstance(
            snapshot.channels[1].details,
            AdbChannelState,
        )

    def test_window_focus_tracks_target_and_foreground_identity(self) -> None:
        with self.assertRaises(ValueError):
            WindowChannelState(
                window_id="hwnd:42",
                foreground_window_id="hwnd:99",
                focus=FocusStatus.TARGET,
            )

        with self.assertRaises(ValueError):
            WindowChannelState(
                window_id="hwnd:42",
                foreground_window_id="hwnd:42",
                focus=FocusStatus.OTHER,
            )

        with self.assertRaises(ValueError):
            WindowChannelState(
                window_id="hwnd:42",
                foreground_window_id="hwnd:42",
                focus=FocusStatus.TARGET,
                minimized=True,
            )

    def test_adb_transport_readiness_requires_online_device(self) -> None:
        with self.assertRaises(ValueError):
            AdbChannelState(
                serial="emulator-5554",
                server_reachable=True,
                device_status=AdbDeviceStatus.UNAUTHORIZED,
                transport_ready=True,
            )

        with self.assertRaises(ValueError):
            AdbChannelState(
                server_reachable=True,
                device_status=AdbDeviceStatus.ONLINE,
                transport_ready=True,
            )

    def test_channel_status_and_details_are_consistent(self) -> None:
        with self.assertRaises(ValueError):
            ControlChannelSnapshot(
                channel_id=ControlChannelId("desktop"),
                kind=ControlChannelKind.DESKTOP_WINDOW,
                status=ControlChannelStatus.READY,
                blockers=(ReadinessBlocker("window.not_foreground"),),
                details=WindowChannelState(),
            )

        with self.assertRaises(ValueError):
            ControlChannelSnapshot(
                channel_id=ControlChannelId("adb"),
                kind=ControlChannelKind.ADB,
                status=ControlChannelStatus.BLOCKED,
                details=AdbChannelState(),
            )

        with self.assertRaises(TypeError):
            ControlChannelSnapshot(
                channel_id=ControlChannelId("adb"),
                kind=ControlChannelKind.ADB,
                status=ControlChannelStatus.UNKNOWN,
                details=WindowChannelState(),
            )

    def test_snapshot_rejects_duplicate_channels_and_missing_ready_target(
        self,
    ) -> None:
        window = self._window_channel()
        with self.assertRaises(ValueError):
            TargetRuntimeSnapshot(
                target_id=TargetId("game"),
                observed_at=datetime.now(timezone.utc),
                availability=TargetAvailability.AVAILABLE,
                inspector_id="test",
                channels=(window, window),
            )

        with self.assertRaises(ValueError):
            TargetRuntimeSnapshot(
                target_id=TargetId("game"),
                observed_at=datetime.now(timezone.utc),
                availability=TargetAvailability.MISSING,
                inspector_id="test",
                channels=(window,),
            )

    def test_runtime_models_are_immutable(self) -> None:
        snapshot = TargetRuntimeSnapshot(
            target_id=TargetId("game"),
            observed_at=datetime.now(timezone.utc),
            availability=TargetAvailability.AVAILABLE,
            inspector_id="test",
            channels=(self._window_channel(),),
        )

        with self.assertRaises(FrozenInstanceError):
            snapshot.availability = TargetAvailability.MISSING

    def test_snapshot_requires_timezone_aware_time(self) -> None:
        with self.assertRaises(ValueError):
            TargetRuntimeSnapshot(
                target_id=TargetId("game"),
                observed_at=datetime(2026, 7, 28),
                availability=TargetAvailability.UNKNOWN,
                inspector_id="test",
            )


if __name__ == "__main__":
    unittest.main()
