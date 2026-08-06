from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
import unittest

from adb.observation import (
    AdbChannelInspector,
    AdbChannelState,
    AdbDeviceStatus,
)
from desktop_window.observation import (
    FocusStatus,
    WindowChannelInspector,
    WindowChannelState,
)
from observation.target_runtime import (
    ControlChannelId,
    ControlChannelKind,
    ControlChannelSnapshot,
    ControlChannelStatus,
    TargetAvailability,
    TargetId,
    TargetRuntimeSnapshot,
)


class StaticWindowInspector:
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


class StaticAdbInspector:
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


class PlatformObservationMigrationTest(unittest.TestCase):
    def test_canonical_platform_packages_specialize_core_contracts(self) -> None:
        window = ControlChannelSnapshot(
            channel_id=ControlChannelId("window"),
            kind=ControlChannelKind.DESKTOP_WINDOW,
            status=ControlChannelStatus.READY,
            details=WindowChannelState(
                window_id="hwnd:42",
                foreground_window_id="hwnd:42",
                focus=FocusStatus.TARGET,
                minimized=False,
            ),
        )
        adb = ControlChannelSnapshot(
            channel_id=ControlChannelId("adb:emulator-5554"),
            kind=ControlChannelKind.ADB,
            status=ControlChannelStatus.UNKNOWN,
            details=AdbChannelState(
                serial="emulator-5554",
                server_reachable=True,
                device_status=AdbDeviceStatus.ONLINE,
                transport_ready=True,
            ),
        )
        target_id = TargetId("emulator")
        window_inspector: WindowChannelInspector = StaticWindowInspector(window)
        adb_inspector: AdbChannelInspector = StaticAdbInspector(adb)

        runtime = TargetRuntimeSnapshot(
            target_id=target_id,
            observed_at=datetime(2026, 8, 6, tzinfo=timezone.utc),
            availability=TargetAvailability.AVAILABLE,
            inspector_id="composite",
            channels=(
                window_inspector.inspect(target_id),
                adb_inspector.inspect(target_id),
            ),
        )

        self.assertIs(runtime.channels[0].details, window.details)
        self.assertIs(runtime.channels[1].details, adb.details)

    def test_legacy_import_paths_alias_canonical_objects(self) -> None:
        from observation.target_runtime import (
            AdbChannelInspector as LegacyAdbChannelInspector,
            AdbChannelState as LegacyAdbChannelState,
            AdbDeviceStatus as LegacyAdbDeviceStatus,
            FocusStatus as LegacyFocusStatus,
            WindowChannelInspector as LegacyWindowChannelInspector,
            WindowChannelState as LegacyWindowChannelState,
        )
        from observation.target_runtime.domain import (
            AdbChannelState as LegacyDomainAdbChannelState,
            AdbDeviceStatus as LegacyDomainAdbDeviceStatus,
            FocusStatus as LegacyDomainFocusStatus,
            WindowChannelState as LegacyDomainWindowChannelState,
        )
        from observation.target_runtime.domain.channels import (
            AdbChannelState as LegacyChannelsAdbChannelState,
            WindowChannelState as LegacyChannelsWindowChannelState,
        )
        from observation.target_runtime.domain.readiness import (
            AdbDeviceStatus as LegacyReadinessAdbDeviceStatus,
            FocusStatus as LegacyReadinessFocusStatus,
        )
        from observation.target_runtime.ports import (
            AdbChannelInspector as LegacyPortsAdbChannelInspector,
            WindowChannelInspector as LegacyPortsWindowChannelInspector,
        )

        self.assertIs(LegacyAdbChannelState, AdbChannelState)
        self.assertIs(LegacyDomainAdbChannelState, AdbChannelState)
        self.assertIs(LegacyChannelsAdbChannelState, AdbChannelState)
        self.assertIs(LegacyAdbDeviceStatus, AdbDeviceStatus)
        self.assertIs(LegacyDomainAdbDeviceStatus, AdbDeviceStatus)
        self.assertIs(LegacyReadinessAdbDeviceStatus, AdbDeviceStatus)
        self.assertIs(LegacyAdbChannelInspector, AdbChannelInspector)
        self.assertIs(LegacyPortsAdbChannelInspector, AdbChannelInspector)
        self.assertIs(LegacyWindowChannelState, WindowChannelState)
        self.assertIs(LegacyDomainWindowChannelState, WindowChannelState)
        self.assertIs(LegacyChannelsWindowChannelState, WindowChannelState)
        self.assertIs(LegacyFocusStatus, FocusStatus)
        self.assertIs(LegacyDomainFocusStatus, FocusStatus)
        self.assertIs(LegacyReadinessFocusStatus, FocusStatus)
        self.assertIs(LegacyWindowChannelInspector, WindowChannelInspector)
        self.assertIs(LegacyPortsWindowChannelInspector, WindowChannelInspector)

    def test_importing_core_contracts_does_not_load_platform_modules(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        script = """
import sys
import observation.target_runtime
assert 'adb.observation.domain' not in sys.modules
assert 'adb.observation.ports' not in sys.modules
assert 'desktop_window.observation.domain' not in sys.modules
assert 'desktop_window.observation.ports' not in sys.modules
"""
        subprocess.run(
            [sys.executable, "-c", script],
            cwd=repository_root,
            check=True,
        )


if __name__ == "__main__":
    unittest.main()
