"""Public contracts for coordinating independently acquired observations.

Observation is an orchestration boundary, not an alias for visual capture.
`ObservationBundle` can combine Temporal, Capture, and Target Runtime snapshots
for one cycle while preserving each snapshot's own timestamp and domain model.

Capture value types are re-exported here for existing observation consumers. The
source packages remain separate: Capture owns pixel facts, Target Runtime owns
operational target and channel facts, and Temporal owns clock observations.
"""

from capture import (
    CapturedFrame,
    CapturedFrameSource,
    CaptureQuality,
    CaptureStreamId,
    CaptureSurface,
    CoordinateSpace,
    CoordinateTransform,
    FrameId,
    FrameInfo,
    FramePixels,
    PixelFormat,
)
from observation.domain.models import (
    ObservationBundle,
    ObservationCoherence,
)

__all__ = [
    "CapturedFrame",
    "CapturedFrameSource",
    "CaptureQuality",
    "CaptureStreamId",
    "CaptureSurface",
    "CoordinateSpace",
    "CoordinateTransform",
    "FrameId",
    "FrameInfo",
    "FramePixels",
    "ObservationBundle",
    "ObservationCoherence",
    "PixelFormat",
]
