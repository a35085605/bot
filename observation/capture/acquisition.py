from __future__ import annotations

from dataclasses import dataclass

from imaging import materialize_image
from observation.capture.domain.models import AcquiredFrame, CapturedFrame
from observation.capture.ports import FrameCaptureBackend


def materialize_capture(frame: AcquiredFrame) -> CapturedFrame:
    """Cross the capture boundary with independent contiguous pixels."""

    if not isinstance(frame, AcquiredFrame):
        raise TypeError("frame must be AcquiredFrame")

    return CapturedFrame(
        info=frame.info,
        image=materialize_image(frame.image),
        quality=frame.quality,
    )


@dataclass(frozen=True, slots=True)
class MaterializingFrameSource:
    """Public frame source that normalizes a backend acquisition result."""

    backend: FrameCaptureBackend

    def __post_init__(self) -> None:
        if not hasattr(self.backend, "acquire"):
            raise TypeError("backend must provide acquire()")

    def capture(self) -> CapturedFrame:
        acquired = self.backend.acquire()
        if not isinstance(acquired, AcquiredFrame):
            raise TypeError(
                "frame capture backend must return AcquiredFrame"
            )
        return materialize_capture(acquired)
