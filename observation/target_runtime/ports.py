from __future__ import annotations

from typing import Protocol, TypeVar

from observation.target_runtime.domain.channels import ControlChannelSnapshot
from observation.target_runtime.domain.snapshots import TargetRuntimeSnapshot
from target import TargetId


ControlChannelStateT_co = TypeVar(
    "ControlChannelStateT_co",
    covariant=True,
)


class ControlChannelInspector(Protocol[ControlChannelStateT_co]):
    """Read-only observation port for one target control channel.

    Implementations inspect exactly one configured channel and return its latest
    immutable readiness snapshot. They must not prepare the channel, reconnect a
    transport, change focus, or send input.

    Platform and external packages may specialize this protocol with their own
    detail model and ``ControlChannelKind`` value without modifying the core.
    """

    def inspect(
        self,
        target_id: TargetId,
    ) -> ControlChannelSnapshot[ControlChannelStateT_co]:
        """Acquire one channel snapshot for ``target_id``."""
        ...


class TargetRuntimeInspector(Protocol):
    """Read-only observation port for one logical target's runtime state.

    Implementations may inspect processes, windows, ADB, emulator APIs, or test
    doubles to establish target availability and control-channel state. They must
    not launch the target, change focus, reconnect transports, or send input.

    Aggregate implementations may compose per-channel inspectors, but target
    availability remains a separate target-level fact and must not be inferred
    solely from the absence of ready channels.
    """

    def inspect(self, target_id: TargetId) -> TargetRuntimeSnapshot:
        """Acquire one timestamped operational snapshot for ``target_id``."""
        ...


__all__ = [
    "ControlChannelInspector",
    "TargetRuntimeInspector",
]
