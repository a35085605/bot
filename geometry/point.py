from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True, slots=True)
class Point:

    x: int
    y: int

    def as_tuple(self) -> Tuple[int, int]:
        return self.x, self.y


@dataclass(frozen=True, slots=True)
class RelativePoint:

    x_ratio: float
    y_ratio: float

    def clamp(self) -> "RelativePoint":
        return RelativePoint(
            x_ratio=max(0.0, min(1.0, float(self.x_ratio))),
            y_ratio=max(0.0, min(1.0, float(self.y_ratio))),
        )

    def to_point(self, *, width: int, height: int) -> Point:
        if width <= 0 or height <= 0:
            raise ValueError(f"width/height must be positive integers, received {width}x{height}")
        c = self.clamp()
        x = int(round(c.x_ratio * width))
        y = int(round(c.y_ratio * height))
        x = max(0, min(x, width - 1))
        y = max(0, min(y, height - 1))
        return Point(x=x, y=y)
