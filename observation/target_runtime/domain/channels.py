from __future__ import annotations

from dataclasses import dataclass, field
from numbers import Integral
from typing import Generic, TypeAlias, TypeVar

from geometry.rect import Rect
from observation.target_runtime.domain.identities import (
    ControlChannelId,
    ReadinessBlocker,
    normalize_optional_text,
)
from observation.target_runtime.domain.readiness import (
    AdbDeviceStatus,
    ControlCapability,
    ControlChannelKind,
    ControlChannelStatus,
    FocusStatus,
)


def _validate_optional_bool(
    value: object,
    *,
    field_name: str,
) -> bool | None:
    if value is not None and not isinstance(value, bool):
        raise TypeError(f"{field_name} must be bool or None")
    return value


def _validate_optional_process_id(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise TypeError("window process id must be an integer or None")
    normalized = int(value)
    if normalized <= 0:
        raise ValueError("window process id must be greater than zero")
    return normalized


def _validate_optional_rect(
    value: object,
    *,
    field_name: str,
) -> Rect | None:
    if value is not None and not isinstance(value, Rect):
        raise TypeError(f"{field_name} must be Rect or None")
    return value


@dataclass(frozen=True, slots=True)
class WindowChannelState:
    """Latest observed desktop-window state for one control channel."""

    window_id: str | None = None
    foreground_window_id: str | None = None
    process_id: int | None = None
    title: str | None = None
    client_bounds_screen: Rect | None = None
    window_bounds_screen: Rect | None = None
    focus: FocusStatus = FocusStatus.UNKNOWN
    minimized: bool | None = None
    visible: bool | None = None
    responsive: bool | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.focus, FocusStatus):
            raise TypeError("window focus must be FocusStatus")

        window_id = normalize_optional_text(
            self.window_id,
            field_name="window id",
        )
        foreground_window_id = normalize_optional_text(
            self.foreground_window_id,
            field_name="foreground window id",
        )
        process_id = _validate_optional_process_id(self.process_id)
        title = normalize_optional_text(
            self.title,
            field_name="window title",
        )
        client_bounds_screen = _validate_optional_rect(
            self.client_bounds_screen,
            field_name="window client bounds",
        )
        window_bounds_screen = _validate_optional_rect(
            self.window_bounds_screen,
            field_name="window bounds",
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

        if (
            window_bounds_screen is not None
            and client_bounds_screen is not None
            and not window_bounds_screen.contains_rect(client_bounds_screen)
        ):
            raise ValueError("window bounds must contain client bounds")

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

        object.__setattr__(self, "window_id", window_id)
        object.__setattr__(
            self,
            "foreground_window_id",
            foreground_window_id,
        )
        object.__setattr__(self, "process_id", process_id)
        object.__setattr__(self, "title", title)
        object.__setattr__(
            self,
            "client_bounds_screen",
            client_bounds_screen,
        )
        object.__setattr__(
            self,
            "window_bounds_screen",
            window_bounds_screen,
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

        serial = normalize_optional_text(
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
ControlChannelStateT_co = TypeVar(
    "ControlChannelStateT_co",
    bound=ControlChannelDetails,
    covariant=True,
)


@dataclass(frozen=True, slots=True)
class ControlChannelSnapshot(Generic[ControlChannelStateT_co]):
    """Immutable readiness snapshot for one target control channel."""

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
