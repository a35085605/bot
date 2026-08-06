from __future__ import annotations

from typing import Protocol

from execution.lifecycle.domain import (
    TargetClose,
    TargetLaunch,
    TargetRestart,
    TargetTermination,
)
from native_operation import NativeOperationResult


class TargetLauncher(Protocol):
    def launch(self, operation: TargetLaunch) -> NativeOperationResult:
        ...


class TargetCloser(Protocol):
    def close(self, operation: TargetClose) -> NativeOperationResult:
        ...


class TargetTerminator(Protocol):
    def terminate(self, operation: TargetTermination) -> NativeOperationResult:
        ...


class TargetRestarter(Protocol):
    def restart(self, operation: TargetRestart) -> NativeOperationResult:
        ...
