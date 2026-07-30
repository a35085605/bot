from __future__ import annotations

from typing import Protocol

from capture.domain.models import AcquiredFrame, CapturedFrame


class FrameCaptureBackend(Protocol):
    """Acquire one backend frame before ownership normalization."""

    def acquire(self) -> AcquiredFrame:
        ...


class CapturedFrameSource(Protocol):
    """Capture one materialized pixel frame for application consumers."""

    def capture(self) -> CapturedFrame:
        ...
