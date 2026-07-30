from __future__ import annotations

from typing import Protocol

from execution.control import ExecutionOperationResult
from execution.lifecycle.domain import (
    TargetClose,
    TargetLaunch,
    TargetRestart,
    TargetTermination,
)


class TargetLauncher(Protocol):
    def launch(self, operation: TargetLaunch) -> ExecutionOperationResult:
        ...


class TargetCloser(Protocol):
    def close(self, operation: TargetClose) -> ExecutionOperationResult:
        ...


class TargetTerminator(Protocol):
    def terminate(self, operation: TargetTermination) -> ExecutionOperationResult:
        ...


class TargetRestarter(Protocol):
    def restart(self, operation: TargetRestart) -> ExecutionOperationResult:
        ...
