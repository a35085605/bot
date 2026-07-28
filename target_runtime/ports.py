from __future__ import annotations

from typing import Protocol

from target_runtime.domain.identities import TargetId
from target_runtime.domain.snapshots import TargetRuntimeSnapshot


class TargetRuntimeInspector(Protocol):
    """Observe operational state without changing the target environment."""

    def inspect(self, target_id: TargetId) -> TargetRuntimeSnapshot:
        ...
