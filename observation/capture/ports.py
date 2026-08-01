from __future__ import annotations

from typing import Protocol, TypeAlias

from observation.capture.domain.models import AcquiredFrame, CapturedFrame
from observation.capture.domain.requirements import (
    CaptureBackendProfile,
    CaptureUnavailable,
)


AcquiredFrameResult: TypeAlias = AcquiredFrame | CaptureUnavailable
CapturedFrameResult: TypeAlias = CapturedFrame | CaptureUnavailable


class FrameCaptureBackend(Protocol):
    """Platform-facing port for acquiring one visual observation.

    The backend may use Window, ADB, or another platform mechanism to locate the
    pixel source, but its result contains capture facts only. Current focus,
    process, transport, and control readiness belong to Target Runtime.

    Capture availability cannot be guaranteed inside this boundary. Expected
    blockers are returned as ``CaptureUnavailable`` values so orchestration can
    decide whether to prepare the environment, retry, wait, or stop.
    """

    @property
    def profile(self) -> CaptureBackendProfile:
        """Declare the backend identity and static technical requirements."""
        ...

    def acquire(self) -> AcquiredFrameResult:
        """Acquire one backend frame or describe why it is unavailable."""
        ...


class CapturedFrameSource(Protocol):
    """Application-facing source of materialized capture results.

    Successful results contain immutable visual observations with owned
    contiguous pixels. Unavailable results preserve expected capture blockers.
    A source is not a complete observation cycle and does not imply that the
    logical target exists or can currently be controlled.
    """

    @property
    def profile(self) -> CaptureBackendProfile:
        """Expose the underlying capture mechanism's static profile."""
        ...

    def capture(self) -> CapturedFrameResult:
        """Return one materialized frame or a typed unavailable result."""
        ...
