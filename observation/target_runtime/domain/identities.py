from __future__ import annotations

from dataclasses import dataclass


def normalize_non_empty_text(
    value: object,
    *,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise TypeError(
            f"{field_name} must be a string, "
            f"got {type(value).__name__}"
        )

    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} cannot be empty")
    return normalized


def normalize_optional_text(
    value: object,
    *,
    field_name: str,
) -> str | None:
    if value is None:
        return None
    return normalize_non_empty_text(value, field_name=field_name)


@dataclass(frozen=True, slots=True, order=True)
class TargetId:
    """Stable identity of one logical automation target."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            normalize_non_empty_text(
                self.value,
                field_name="target id",
            ),
        )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True, order=True)
class ControlChannelId:
    """Stable identity of one control channel for a target."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            normalize_non_empty_text(
                self.value,
                field_name="control channel id",
            ),
        )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True, order=True)
class ReadinessBlocker:
    """Stable machine-readable reason that prevents channel readiness."""

    code: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "code",
            normalize_non_empty_text(
                self.code,
                field_name="readiness blocker code",
            ),
        )

    def __str__(self) -> str:
        return self.code
