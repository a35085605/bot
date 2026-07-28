from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TypeAlias


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


def _normalize_optional_text(
    value: object,
    *,
    field_name: str,
) -> str | None:
    if value is None:
        return None
    return _normalize_non_empty_text(value, field_name=field_name)


def _validate_optional_bool(
    value: object,
    *,
    field_name: str,
) -> bool | None:
    if value is not None and not isinstance(value, bool):
        raise TypeError(f"{field_name} must be bool or None")
    return value


@dataclass(frozen=True, slots=True, order=True)
class TargetId:
    """Stable identity of one logical automation target."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_non_empty_text(
                self.value,
                field_name="target id",
            ),
        )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True, order=True)
class ControlChannelId:
    """Stable identity of one control channel for a target."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_non_empty_text(
                self.value,
                field_name="control channel id",
            ),
        )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True, order=True)
class ReadinessBlocker:
    """Stable machine-readable reason that prevents channel readiness."""

    code: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "code",
            _normalize_non_empty_text(
                self.code,
                field_name="readiness blocker code",
            ),
        )

    def __str__(self) -> str:
        return self.code


class TargetAvailability(str, Enum):
    UNKNOWN = "unknown"
    MISSING = "missing"
    AVAILABLE = "available"


class ControlChannelKind(str, Enum):
    DESKTOP_WINDOW = "desktop_window"
    ADB = "adb"


class ControlChannelStatus(str, Enum):
    UNKNOWN = "unknown"
    UNAVAILABLE = "unavailable"
    BLOCKED = "blocked"
    READY = "ready"


class ControlCapability(str, Enum):
    POINTER = "pointer"
    KEYBOARD = "keyboard"
    TEXT = "text"
    BACK = "back"


class FocusStatus(str, Enum):
    UNKNOWN = "unknown"
    TARGET = "target"
    OTHER = "other"
    NONE = "none"
    NOT_REQUIRED = "not_required"


class AdbDeviceStatus(str, Enum):
    UNKNOWN = "unknown"
    MISSING = "missing"
    UNAUTHORIZED = "unauthorized"
    OFFLINE = "offline"
    ONLINE = "online"


@dataclass(frozen=True, slots=True)
class WindowChannelState:
    """Observed desktop-window state for one control channel."""

    window_id: str | None = None
    foreground_window_id: str | None = None
    focus: FocusStatus = FocusStatus.UNKNOWN
    minimized: bool | None = None
    visible: bool | None = None
    responsive: bool | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.focus, FocusStatus):
            raise TypeError("window focus must be FocusStatus")

        window_id = _normalize_optional_text(
            self.window_id,
            field_name="window id",
        )
        foreground_window_id = _normalize_optional_text(
            self.foreground_window_id,
            field_name="foreground window id",
        )
        minimized = _validate_optional_bool(
            self.minimized,
            field_name="window minimized",
        )
        visible = _validate_optional_bool(
            self.visible,
            field_name="window visible",
        )
        responsive = _validate_optional_bool(
            self.responsive,
            field_name="window responsive",
        )

        if self.focus is FocusStatus.TARGET:
            if window_id is None or foreground_window_id is None:
                raise ValueError(
                    "target focus requires target and foreground window ids"
                )
            if window_id != foreground_window_id:
                raise ValueError(
                    "target focus requires the target window to be foreground"
                )
            if minimized is True:
                raise ValueError(
                    "a minimized window cannot hold target focus"
                )
        elif self.focus is FocusStatus.OTHER:
            if foreground_window_id is None:
                raise ValueError(
                    "other focus requires a foreground window id"
                )
            if window_id is not None and window_id == foreground_window_id:
                raise ValueError(
                    "other focus cannot name the target as foreground"
                )
        elif self.focus is FocusStatus.NONE:
            if foreground_window_id is not None:
                raise ValueError(
                    "no focus cannot include a foreground window id"
                )
        elif self.focus is FocusStatus.NOT_REQUIRED:
            raise ValueError(
                "desktop window focus cannot be marked not required"
            )

        object.__setattr__(self, "window_id", window_id)
        object.__setattr__(
            self,
            "foreground_window_id",
            foreground_window_id,
        )
        object.__setattr__(self, "minimized", minimized)
        object.__setattr__(self, "visible", visible)
        object.__setattr__(self, "responsive", responsive)


@dataclass(frozen=True, slots=True)
class AdbChannelState:
    """Observed ADB server, device, and transport state."""

    serial: str | None = None
    server_reachable: bool | None = None
    device_status: AdbDeviceStatus = AdbDeviceStatus.UNKNOWN
    transport_ready: bool | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.device_status, AdbDeviceStatus):
            raise TypeError("ADB device status must be AdbDeviceStatus")

        serial = _normalize_optional_text(
            self.serial,
            field_name="ADB device serial",
        )
        server_reachable = _validate_optional_bool(
            self.server_reachable,
            field_name="ADB server reachable",
        )
        transport_ready = _validate_optional_bool(
            self.transport_ready,
            field_name="ADB transport ready",
        )

        if self.device_status is AdbDeviceStatus.ONLINE and serial is None:
            raise ValueError("an online ADB device requires a serial")
        if transport_ready is True:
            if server_reachable is not True:
                raise ValueError(
                    "a ready ADB transport requires a reachable server"
                )
            if self.device_status is not AdbDeviceStatus.ONLINE:
                raise ValueError(
                    "a ready ADB transport requires an online device"
                )

        object.__setattr__(self, "serial", serial)
        object.__setattr__(
            self,
            "server_reachable",
            server_reachable,
        )
        object.__setattr__(self, "transport_ready", transport_ready)


ControlChannelDetails: TypeAlias = WindowChannelState | AdbChannelState


@dataclass(frozen=True, slots=True)
class ControlChannelSnapshot:
    """Immutable readiness snapshot for one target control channel."""

    channel_id: ControlChannelId
    kind: ControlChannelKind
    status: ControlChannelStatus
    details: ControlChannelDetails
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
        if not isinstance(self.capabilities, frozenset):
            raise TypeError("channel capabilities must be a frozenset")
        if not isinstance(self.blockers, tuple):
            raise TypeError("channel blockers must be a tuple")

        expected_detail_type = {
            ControlChannelKind.DESKTOP_WINDOW: WindowChannelState,
            ControlChannelKind.ADB: AdbChannelState,
        }[self.kind]
        if not isinstance(self.details, expected_detail_type):
            raise TypeError(
                f"{self.kind.value} channel requires "
                f"{expected_detail_type.__name__}"
            )

        for capability in self.capabilities:
            if not isinstance(capability, ControlCapability):
                raise TypeError(
                    "channel capabilities must contain "
                    "ControlCapability values"
                )
        for index, blocker in enumerate(self.blockers):
            if not isinstance(blocker, ReadinessBlocker):
                raise TypeError(
                    f"channel blockers[{index}] must be ReadinessBlocker"
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
