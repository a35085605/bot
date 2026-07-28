from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from target_runtime.domain.channels import ControlChannelSnapshot
from target_runtime.domain.identities import (
    ControlChannelId,
    TargetId,
    normalize_non_empty_text,
)
from target_runtime.domain.readiness import (
    ControlCapability,
    ControlChannelStatus,
    TargetAvailability,
)


@dataclass(frozen=True, slots=True)
class TargetRuntimeSnapshot:
    """Latest observed operational state for one logical target."""

    target_id: TargetId
    observed_at: datetime
    availability: TargetAvailability
    inspector_id: str
    channels: tuple[ControlChannelSnapshot, ...] = field(
        default_factory=tuple
    )

    def __post_init__(self) -> None:
        if not isinstance(self.target_id, TargetId):
            raise TypeError("target_id must be TargetId")
        if not isinstance(self.observed_at, datetime):
            raise TypeError("observed_at must be datetime")
        if self.observed_at.utcoffset() is None:
            raise ValueError("observed_at must be timezone-aware")
        if not isinstance(self.availability, TargetAvailability):
            raise TypeError("availability must be TargetAvailability")
        if not isinstance(self.channels, tuple):
            raise TypeError("channels must be a tuple")

        inspector_id = normalize_non_empty_text(
            self.inspector_id,
            field_name="runtime inspector id",
        )

        channel_ids: set[ControlChannelId] = set()
        for index, channel in enumerate(self.channels):
            if not isinstance(channel, ControlChannelSnapshot):
                raise TypeError(
                    f"channels[{index}] must be ControlChannelSnapshot"
                )
            if channel.channel_id in channel_ids:
                raise ValueError(
                    "target runtime channels must have unique ids"
                )
            channel_ids.add(channel.channel_id)

        if self.availability is TargetAvailability.MISSING:
            if any(
                channel.status is ControlChannelStatus.READY
                for channel in self.channels
            ):
                raise ValueError(
                    "a missing target cannot have a ready control channel"
                )

        object.__setattr__(self, "inspector_id", inspector_id)

    def channel(
        self,
        channel_id: ControlChannelId,
    ) -> ControlChannelSnapshot | None:
        if not isinstance(channel_id, ControlChannelId):
            raise TypeError("channel_id must be ControlChannelId")
        return next(
            (
                channel
                for channel in self.channels
                if channel.channel_id == channel_id
            ),
            None,
        )

    @property
    def ready_channels(self) -> tuple[ControlChannelSnapshot, ...]:
        return tuple(
            channel
            for channel in self.channels
            if channel.status is ControlChannelStatus.READY
        )

    def supports(self, capability: ControlCapability) -> bool:
        if not isinstance(capability, ControlCapability):
            raise TypeError("capability must be ControlCapability")
        return any(
            channel.supports(capability)
            for channel in self.ready_channels
        )
