from __future__ import annotations

from typing import Protocol

from adb.management.domain import (
    AdbServerStart,
    AdbServerStop,
    AdbTransportPreparation,
    AdbTransportRecovery,
)
from native_operation import NativeOperationResult


class AdbServerStarter(Protocol):
    def start(self, operation: AdbServerStart) -> NativeOperationResult:
        ...


class AdbServerStopper(Protocol):
    def stop(self, operation: AdbServerStop) -> NativeOperationResult:
        ...


class AdbTransportPreparer(Protocol):
    def prepare(
        self,
        operation: AdbTransportPreparation,
    ) -> NativeOperationResult:
        ...


class AdbTransportRecoverer(Protocol):
    def recover(
        self,
        operation: AdbTransportRecovery,
    ) -> NativeOperationResult:
        ...
