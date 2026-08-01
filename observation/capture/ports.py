from __future__ import annotations

from typing import Protocol, TypeAlias

from observation.capture.domain.models import AcquiredFrame, CapturedFrame
from observation.capture.domain.requirements import (
    CaptureBackendProfile,
    CaptureUnavailable,
)


CaptureAcquisitionAttempt: TypeAlias = AcquiredFrame | CaptureUnavailable
CapturedFrameAttempt: TypeAlias = CapturedFrame | CaptureUnavailable


class FrameCaptureBackend(Protocol):
    """Platform-facing port for acquiring one visual observation.

    The backend may use Window, ADB, or another platform mechanism to locate the
    pixel source, but its result contains capture facts only. Current focus,
    process, transport, and control readiness belong to Target Runtime.
    """

    def acquire(self) -> AcquiredFrame:
        """Acquire one backend frame before pixel-ownership normalization."""
        ...


class CapturedFrameSource(Protocol):
    """Application-facing source of materialized captured frames.

    A returned ``CapturedFrame`` is an immutable visual observation with owned
    contiguous pixels. It is not a complete observation cycle and does not imply
    that the logical target exists or can currently be controlled.
    """

    def capture(self) -> CapturedFrame:
        """Return one materialized frame for application consumers."""
        ...


class ConditionalFrameCaptureBackend(Protocol):
    """Capture backend that declares requirements and may be unavailable.

    Implementations may inspect platform facts needed by their capture
    mechanism, but must not restore, activate, raise, or otherwise mutate the
    target environment. Expected runtime blockers are returned as
    ``CaptureUnavailable`` values.
    """

    @property
    def profile(self) -> CaptureBackendProfile:
        ...

    def try_acquire(self) -> CaptureAcquisitionAttempt:
        """Acquire one frame or describe why acquisition is unavailable."""
        ...


class ConditionalCapturedFrameSource(Protocol):
    """Application-facing conditional source of materialized frames."""

    @property
    def profile(self) -> CaptureBackendProfile:
        ...

    def try_capture(self) -> CapturedFrameAttempt:
        """Return a materialized frame or a typed unavailable result."""
        ...
