from __future__ import annotations

from dataclasses import dataclass

from target import TargetId


def _require_target_id(value: object) -> TargetId:
    if not isinstance(value, TargetId):
        raise TypeError("target_id must be TargetId")
    return value


@dataclass(frozen=True, slots=True)
class TargetLaunch:
    target_id: TargetId

    def __post_init__(self) -> None:
        _require_target_id(self.target_id)


@dataclass(frozen=True, slots=True)
class TargetClose:
    """Request an orderly target shutdown."""

    target_id: TargetId

    def __post_init__(self) -> None:
        _require_target_id(self.target_id)


@dataclass(frozen=True, slots=True)
class TargetTermination:
    """Request forced target termination."""

    target_id: TargetId

    def __post_init__(self) -> None:
        _require_target_id(self.target_id)


@dataclass(frozen=True, slots=True)
class TargetRestart:
    """Request a target restart through a native or composed implementation."""

    target_id: TargetId

    def __post_init__(self) -> None:
        _require_target_id(self.target_id)
