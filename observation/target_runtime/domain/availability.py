from enum import Enum


class TargetAvailability(str, Enum):
    UNKNOWN = "unknown"
    MISSING = "missing"
    AVAILABLE = "available"


__all__ = ["TargetAvailability"]
