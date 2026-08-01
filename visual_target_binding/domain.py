from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import math
from numbers import Real
from typing import TypeAlias

from geometry.rect import Rect
from observation.capture import FrameId
from observation.target_runtime import ControlChannelId, TargetId


def _normalize_non_empty_text(value: object, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(
            f"{field_name} must be a string, got {type(value).__name__}"
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


def _normalize_confidence(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError("binding confidence must be a real number")
    normalized = float(value)
    if not math.isfinite(normalized):
        raise ValueError("binding confidence must be finite")
    if not 0.0 <= normalized <= 1.0:
        raise ValueError("binding confidence must be between 0 and 1")
    return normalized


class VisualTargetBindingBasis(str, Enum):
    CAPTURE_REQUEST = "capture_request"
    NATIVE_SURFACE_IDENTITY = "native_surface_identity"
    DEVICE_DISPLAY_IDENTITY = "device_display_identity"
    GEOMETRY_MATCH = "geometry_match"
    VISUAL_RECOGNITION = "visual_recognition"


@dataclass(frozen=True, slots=True)
class VisualTargetBinding:
    """Historical association between visual content and a logical target.

    The binding records why one content region was associated with one target at
    ``established_at``. It does not claim that the target or channel still exists,
    remains ready, or retains compatible geometry. Execution must inspect and
    revalidate current Target Runtime state before a side effect.
    """

    frame_id: FrameId
    source_id: str
    content_bounds: Rect
    target_id: TargetId
    established_at: datetime
    basis: VisualTargetBindingBasis
    confidence: float
    channel_id: ControlChannelId | None = None
    capture_surface_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.frame_id, FrameId):
            raise TypeError("binding frame_id must be FrameId")
        if not isinstance(self.content_bounds, Rect):
            raise TypeError("binding content_bounds must be Rect")
        if not isinstance(self.target_id, TargetId):
            raise TypeError("binding target_id must be TargetId")
        if not isinstance(self.established_at, datetime):
            raise TypeError("binding established_at must be datetime")
        if self.established_at.utcoffset() is None:
            raise ValueError("binding established_at must be timezone-aware")
        if not isinstance(self.basis, VisualTargetBindingBasis):
            raise TypeError("binding basis must be VisualTargetBindingBasis")
        if self.channel_id is not None and not isinstance(
            self.channel_id,
            ControlChannelId,
        ):
            raise TypeError("binding channel_id must be ControlChannelId or None")
        object.__setattr__(
            self,
            "source_id",
            _normalize_non_empty_text(
                self.source_id,
                field_name="binding source id",
            ),
        )
        object.__setattr__(
            self,
            "capture_surface_id",
            _normalize_optional_text(
                self.capture_surface_id,
                field_name="binding capture surface id",
            ),
        )
        object.__setattr__(
            self,
            "confidence",
            _normalize_confidence(self.confidence),
        )


class VisualTargetBindingFailureReason(str, Enum):
    TARGET_UNAVAILABLE = "target_unavailable"
    SOURCE_AMBIGUOUS = "source_ambiguous"
    IDENTITY_MISMATCH = "identity_mismatch"
    GEOMETRY_MISMATCH = "geometry_mismatch"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True, slots=True)
class VisualTargetBindingUnavailable:
    reason: VisualTargetBindingFailureReason
    diagnostic: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.reason, VisualTargetBindingFailureReason):
            raise TypeError(
                "binding unavailable reason must be "
                "VisualTargetBindingFailureReason"
            )
        object.__setattr__(
            self,
            "diagnostic",
            _normalize_optional_text(
                self.diagnostic,
                field_name="binding diagnostic",
            ),
        )


VisualTargetBindingResult: TypeAlias = (
    VisualTargetBinding | VisualTargetBindingUnavailable
)
