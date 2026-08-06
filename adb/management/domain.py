from __future__ import annotations

from dataclasses import dataclass

from control_channel import ControlChannelId


@dataclass(frozen=True, slots=True)
class AdbServerStart:
    """Request that the configured ADB server be made reachable."""


@dataclass(frozen=True, slots=True)
class AdbServerStop:
    """Request an orderly stop of the configured ADB server."""


@dataclass(frozen=True, slots=True)
class AdbTransportPreparation:
    """Request that one configured ADB control channel become usable."""

    channel_id: ControlChannelId

    def __post_init__(self) -> None:
        if not isinstance(self.channel_id, ControlChannelId):
            raise TypeError("channel_id must be ControlChannelId")


@dataclass(frozen=True, slots=True)
class AdbTransportRecovery:
    """Request recovery of a previously configured ADB control channel."""

    channel_id: ControlChannelId

    def __post_init__(self) -> None:
        if not isinstance(self.channel_id, ControlChannelId):
            raise TypeError("channel_id must be ControlChannelId")
