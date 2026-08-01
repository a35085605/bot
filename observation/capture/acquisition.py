from __future__ import annotations

from dataclasses import dataclass

from imaging import materialize_image
from observation.capture.domain.models import AcquiredFrame, CapturedFrame
from observation.capture.domain.requirements import (
    CaptureBackendProfile,
    CaptureUnavailable,
)
from observation.capture.ports import CapturedFrameResult, FrameCaptureBackend


def materialize_acquired_frame(frame: AcquiredFrame) -> CapturedFrame:
    """Cross the capture boundary with independent contiguous pixels."""

    if not isinstance(frame, AcquiredFrame):
        raise TypeError("frame must be AcquiredFrame")

    return CapturedFrame(
        info=frame.info,
        image=materialize_image(frame.image),
        quality=frame.quality,
    )


def _validate_unavailable(
    unavailable: CaptureUnavailable,
    *,
    profile: CaptureBackendProfile,
) -> None:
    if unavailable.backend_id != profile.backend_id:
        raise ValueError(
            "capture unavailable backend_id must match backend profile"
        )
    undeclared = set(unavailable.unmet_requirements).difference(
        profile.requirements
    )
    if undeclared:
        raise ValueError(
            "capture unavailable contains requirements not declared "
            "by the backend profile"
        )


@dataclass(frozen=True, slots=True)
class MaterializingFrameSource:
    """Normalize backend capture results at the pixel-ownership boundary."""

    backend: FrameCaptureBackend

    def __post_init__(self) -> None:
        if not hasattr(self.backend, "profile"):
            raise TypeError("backend must provide profile")
        if not hasattr(self.backend, "acquire"):
            raise TypeError("backend must provide acquire()")
        if not isinstance(self.backend.profile, CaptureBackendProfile):
            raise TypeError("backend profile must be CaptureBackendProfile")

    @property
    def profile(self) -> CaptureBackendProfile:
        return self.backend.profile

    def capture(self) -> CapturedFrameResult:
        acquired = self.backend.acquire()
        if isinstance(acquired, CaptureUnavailable):
            _validate_unavailable(acquired, profile=self.profile)
            return acquired
        if not isinstance(acquired, AcquiredFrame):
            raise TypeError(
                "frame capture backend must return AcquiredFrame "
                "or CaptureUnavailable"
            )
        return materialize_acquired_frame(acquired)
