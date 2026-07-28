from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Generic, TypeAlias, TypeVar

from geometry.point import Point
from geometry.rect import Rect
from observation import FrameId
from target_runtime.domain.identities import ControlChannelId, TargetId


NativePointT = TypeVar("NativePointT")


def _normalize_non_empty_text(value: object, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(
            f"{field_name} must be a string, got {type(value).__name__}"
        )
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} cannot be empty")
    return normalized


@dataclass(frozen=True, slots=True)
class ContentPointTarget:
    """A point selected from one semantic content observation."""

    frame_id: FrameId
    source_id: str
    point_content: Point

    def __post_init__(self) -> None:
        if not isinstance(self.frame_id, FrameId):
            raise TypeError("frame_id must be FrameId")
        if not isinstance(self.point_content, Point):
            raise TypeError("point_content must be Point")
        object.__setattr__(
            self,
            "source_id",
            _normalize_non_empty_text(
                self.source_id,
                field_name="content target source id",
            ),
        )


@dataclass(frozen=True, slots=True)
class ContentRectTarget:
    """A rectangle selected from one semantic content observation."""

    frame_id: FrameId
    source_id: str
    bounds_content: Rect

    def __post_init__(self) -> None:
        if not isinstance(self.frame_id, FrameId):
            raise TypeError("frame_id must be FrameId")
        if not isinstance(self.bounds_content, Rect):
            raise TypeError("bounds_content must be Rect")
        object.__setattr__(
            self,
            "source_id",
            _normalize_non_empty_text(
                self.source_id,
                field_name="content target source id",
            ),
        )


class ExecutionTargetFailureReason(str, Enum):
    FRAME_MISMATCH = "frame_mismatch"
    SOURCE_MISMATCH = "source_mismatch"
    TARGET_OUTSIDE_CONTENT = "target_outside_content"
    CHANNEL_NOT_READY = "channel_not_ready"
    CHANNEL_INCOMPATIBLE = "channel_incompatible"
    GEOMETRY_STALE = "geometry_stale"
    GEOMETRY_INCOMPATIBLE = "geometry_incompatible"
    MAPPING_UNAVAILABLE = "mapping_unavailable"


@dataclass(frozen=True, slots=True)
class ExecutionTargetUnavailable:
    reason: ExecutionTargetFailureReason
    diagnostic: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.reason, ExecutionTargetFailureReason):
            raise TypeError("reason must be ExecutionTargetFailureReason")
        if self.diagnostic is not None:
            object.__setattr__(
                self,
                "diagnostic",
                _normalize_non_empty_text(
                    self.diagnostic,
                    field_name="execution target diagnostic",
                ),
            )


@dataclass(frozen=True, slots=True)
class ResolvedExecutionTarget(Generic[NativePointT]):
    """Native target resolved immediately before an external side effect."""

    source_frame_id: FrameId
    source_id: str
    target_id: TargetId
    channel_id: ControlChannelId
    point_native: NativePointT
    resolved_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.source_frame_id, FrameId):
            raise TypeError("source_frame_id must be FrameId")
        if not isinstance(self.target_id, TargetId):
            raise TypeError("target_id must be TargetId")
        if not isinstance(self.channel_id, ControlChannelId):
            raise TypeError("channel_id must be ControlChannelId")
        if self.point_native is None:
            raise TypeError("point_native cannot be None")
        if not isinstance(self.resolved_at, datetime):
            raise TypeError("resolved_at must be datetime")
        if self.resolved_at.utcoffset() is None:
            raise ValueError("resolved_at must be timezone-aware")
        object.__setattr__(
            self,
            "source_id",
            _normalize_non_empty_text(
                self.source_id,
                field_name="resolved target source id",
            ),
        )


ExecutionTargetResolution: TypeAlias = (
    ResolvedExecutionTarget[NativePointT] | ExecutionTargetUnavailable
)
