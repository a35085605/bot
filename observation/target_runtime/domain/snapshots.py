from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from control_channel import (
    ControlCapability,
    ControlChannelId,
    ControlChannelStatus,
)
from observation.target_runtime.domain.availability import TargetAvailability
from observation.target_runtime.domain.channels import ControlChannelSnapshot
from target import TargetId


def _normalize_non_empty_text(
    value: object,
    *,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise TypeError(
            f"{field_name} must be a string, "
            f"got {type(value).__name__}"
        )
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} cannot be empty")
    return normalized


@dataclass(frozen=True, slots=True)
class TargetRuntimeSnapshot:
    """Latest observed operational state for one logical target.

    ``availability`` is a target-level observation. ``channels`` describe the
    independently usable Window, ADB, or future control paths associated with
    that target. A target can therefore be available while every channel is
    blocked or unavailable.

    The snapshot is read-only, time-sensitive evidence for caller-owned
    orchestration and policy. It is not a lock and does not guarantee that the
    same conditions still hold when a management or execution adapter performs
    an external side effect.
    """

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

        inspector_id = _normalize_non_empty_text(
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
        """Return the observed channel with ``channel_id``, when present."""

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
        """Return channels observed as ready at ``observed_at``."""

        return tuple(
            channel
            for channel in self.channels
            if channel.status is ControlChannelStatus.READY
        )

    def supports(self, capability: ControlCapability) -> bool:
        """Whether a currently ready channel reports ``capability``.

        Execution must still revalidate channel readiness before using it.
        """

        if not isinstance(capability, ControlCapability):
            raise TypeError("capability must be ControlCapability")
        return any(
            channel.supports(capability)
            for channel in self.ready_channels
        )
