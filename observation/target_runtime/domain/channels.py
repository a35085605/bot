from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, TypeVar

from control_channel import (
    ControlCapability,
    ControlChannelId,
    ControlChannelKind,
    ControlChannelStatus,
    ReadinessBlocker,
)


ControlChannelStateT_co = TypeVar(
    "ControlChannelStateT_co",
    covariant=True,
)


@dataclass(frozen=True, slots=True)
class ControlChannelSnapshot(Generic[ControlChannelStateT_co]):
    """Immutable readiness snapshot for one target control channel.

    ``details`` is generic and intentionally open to platform and external
    channel packages. A concrete inspector owns the relationship between its
    channel kind and detail model; the interaction kernel enforces only
    platform-neutral snapshot invariants.
    """

    channel_id: ControlChannelId
    kind: ControlChannelKind
    status: ControlChannelStatus
    details: ControlChannelStateT_co
    capabilities: frozenset[ControlCapability] = field(
        default_factory=frozenset
    )
    blockers: tuple[ReadinessBlocker, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not isinstance(self.channel_id, ControlChannelId):
            raise TypeError("channel_id must be ControlChannelId")
        if not isinstance(self.kind, ControlChannelKind):
            raise TypeError("channel kind must be ControlChannelKind")
        if not isinstance(self.status, ControlChannelStatus):
            raise TypeError("channel status must be ControlChannelStatus")
        if self.details is None:
            raise TypeError("channel details cannot be None")
        if not isinstance(self.capabilities, frozenset):
            raise TypeError("channel capabilities must be a frozenset")
        if not isinstance(self.blockers, tuple):
            raise TypeError("channel blockers must be a tuple")

        for capability in self.capabilities:
            if not isinstance(capability, ControlCapability):
                raise TypeError(
                    "channel capabilities must contain "
                    "ControlCapability values"
                )
        for index, blocker in enumerate(self.blockers):
            if not isinstance(blocker, ReadinessBlocker):
                raise TypeError(
                    f"channels blockers[{index}] must be ReadinessBlocker"
                )
        if len(set(self.blockers)) != len(self.blockers):
            raise ValueError("channel blockers cannot contain duplicates")

        if self.status is ControlChannelStatus.READY and self.blockers:
            raise ValueError("a ready channel cannot have blockers")
        if self.status in {
            ControlChannelStatus.BLOCKED,
            ControlChannelStatus.UNAVAILABLE,
        } and not self.blockers:
            raise ValueError(
                "blocked and unavailable channels require a blocker"
            )
        if self.status is ControlChannelStatus.UNKNOWN and self.blockers:
            raise ValueError("an unknown channel cannot assert blockers")

    def supports(self, capability: ControlCapability) -> bool:
        if not isinstance(capability, ControlCapability):
            raise TypeError("capability must be ControlCapability")
        return capability in self.capabilities


__all__ = ["ControlChannelSnapshot"]
