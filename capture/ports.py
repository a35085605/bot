from __future__ import annotations

from typing import Protocol

from capture.domain.models import CapturedFrame


class FrameSource(Protocol):
    """Capture one pixel frame from a concrete visual backend."""

    def capture(self) -> CapturedFrame:
        ...
