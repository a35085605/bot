from __future__ import annotations

from typing import Protocol

from capture.domain.models import AcquiredFrame, CapturedFrame


class FrameCaptureBackend(Protocol):
    """Acquire one backend frame before ownership normalization."""

    def capture(self) -> AcquiredFrame:
        ...


class FrameSource(Protocol):
    """Capture one materialized pixel frame for external consumers."""

    def capture(self) -> CapturedFrame:
        ...
