from __future__ import annotations

from typing import Protocol

from capture.domain.models import AcquiredFrame, CapturedFrame


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
