from __future__ import annotations

from typing import Protocol

from target_runtime.domain.identities import TargetId
from target_runtime.domain.snapshots import TargetRuntimeSnapshot


class TargetRuntimeInspector(Protocol):
    """Read-only observation port for one logical target's runtime state.

    Implementations may inspect processes, windows, ADB, emulator APIs, or test
    doubles to establish target availability and control-channel state. They must
    not launch the target, change focus, reconnect transports, or send input.
    """

    def inspect(self, target_id: TargetId) -> TargetRuntimeSnapshot:
        """Acquire one timestamped operational snapshot for ``target_id``."""
        ...
