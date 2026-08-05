from __future__ import annotations

from typing import Protocol

from execution.control import ExecutionOperationResult
from management.adb.domain import (
    AdbServerStart,
    AdbServerStop,
    AdbTransportPreparation,
    AdbTransportRecovery,
)


class AdbServerStarter(Protocol):
    def start(self, operation: AdbServerStart) -> ExecutionOperationResult:
        ...


class AdbServerStopper(Protocol):
    def stop(self, operation: AdbServerStop) -> ExecutionOperationResult:
        ...


class AdbTransportPreparer(Protocol):
    def prepare(
        self,
        operation: AdbTransportPreparation,
    ) -> ExecutionOperationResult:
        ...


class AdbTransportRecoverer(Protocol):
    def recover(
        self,
        operation: AdbTransportRecovery,
    ) -> ExecutionOperationResult:
        ...
