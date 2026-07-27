from __future__ import annotations

from dataclasses import dataclass


def _normalize_semantic_key(
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


@dataclass(frozen=True, slots=True, order=True)
class SceneKey:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_semantic_key(
                self.value,
                field_name="scene key",
            ),
        )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True, order=True)
class ControlKey:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_semantic_key(
                self.value,
                field_name="control key",
            ),
        )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True, order=True)
class IndicatorKey:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_semantic_key(
                self.value,
                field_name="indicator key",
            ),
        )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True, order=True)
class ValueKey:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_semantic_key(
                self.value,
                field_name="value key",
            ),
        )

    def __str__(self) -> str:
        return self.value
