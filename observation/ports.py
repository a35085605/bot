from __future__ import annotations

from typing import Protocol

from observation.domain.models import CapturedFrame


class FrameSource(Protocol):
    """Capture one observation frame from a concrete backend."""

    def capture(self) -> CapturedFrame:
        ...
