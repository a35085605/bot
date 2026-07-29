from __future__ import annotations

from datetime import datetime
from typing import Protocol


class Clock(Protocol):
    """Injectable source for wall-clock and monotonic time."""

    def now(self) -> datetime:
        ...

    def monotonic(self) -> float:
        ...
