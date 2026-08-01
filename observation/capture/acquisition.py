from __future__ import annotations

from dataclasses import dataclass

from imaging import materialize_image
from observation.capture.domain.models import AcquiredFrame, CapturedFrame
from observation.capture.domain.requirements import (
    CaptureBackendProfile,
    CaptureUnavailable,
)
from observation.capture.ports import (
    CapturedFrameResult,
    ConditionalFrameCaptureBackend,
    FrameCaptureBackend,
)


def materialize_acquired_frame(frame: AcquiredFrame) -> CapturedFrame:
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
        return materialize_acquired_frame(acquired)


@dataclass(frozen=True, slots=True)
class MaterializingConditionalFrameSource:
    """Normalize successful conditional acquisitions without hiding blockers."""

    backend: ConditionalFrameCaptureBackend

    def __post_init__(self) -> None:
        if not hasattr(self.backend, "profile"):
            raise TypeError("backend must provide profile")
        if not hasattr(self.backend, "try_acquire"):
            raise TypeError("backend must provide try_acquire()")
        if not isinstance(self.backend.profile, CaptureBackendProfile):
            raise TypeError("backend profile must be CaptureBackendProfile")

    @property
    def profile(self) -> CaptureBackendProfile:
        return self.backend.profile

    def try_capture(self) -> CapturedFrameResult:
        attempted = self.backend.try_acquire()
        if isinstance(attempted, CaptureUnavailable):
            if attempted.backend_id != self.profile.backend_id:
                raise ValueError(
                    "capture unavailable backend_id must match backend profile"
                )
            undeclared = set(attempted.unmet_requirements).difference(
                self.profile.requirements
            )
            if undeclared:
                raise ValueError(
                    "capture unavailable contains requirements not declared "
                    "by the backend profile"
                )
            return attempted
        if not isinstance(attempted, AcquiredFrame):
            raise TypeError(
                "conditional frame capture backend must return AcquiredFrame "
                "or CaptureUnavailable"
            )
        return materialize_acquired_frame(attempted)
