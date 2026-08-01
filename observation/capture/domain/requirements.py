from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


def _normalize_non_empty_text(value: object, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(
            f"{field_name} must be a string, got {type(value).__name__}"
        )
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} cannot be empty")
    return normalized


def _normalize_optional_text(
    value: object,
    *,
    field_name: str,
) -> str | None:
    if value is None:
        return None
    return _normalize_non_empty_text(value, field_name=field_name)


class CaptureRequirement(str, Enum):
    """One technical precondition required by a capture mechanism."""

    TARGET_AVAILABLE = "target.available"
    WINDOW_VISIBLE = "window.visible"
    WINDOW_NOT_MINIMIZED = "window.not_minimized"
    WINDOW_FOREGROUND = "window.foreground"
    WINDOW_UNOBSCURED = "window.unobscured"
    ADB_TRANSPORT_READY = "adb.transport_ready"


@dataclass(frozen=True, slots=True)
class CaptureBackendProfile:
    """Static technical requirements declared by one capture backend.

    Requirements describe what the backend needs for reliable acquisition. They
    do not grant the backend permission to change the target environment.
    """

    backend_id: str
    requirements: frozenset[CaptureRequirement] = field(
        default_factory=frozenset
    )

    def __post_init__(self) -> None:
        if not isinstance(self.requirements, frozenset):
            raise TypeError("capture requirements must be a frozenset")
        for requirement in self.requirements:
            if not isinstance(requirement, CaptureRequirement):
                raise TypeError(
                    "capture requirements must contain CaptureRequirement "
                    "values"
                )
        object.__setattr__(
            self,
            "backend_id",
            _normalize_non_empty_text(
                self.backend_id,
                field_name="capture backend id",
            ),
        )

    def requires(self, requirement: CaptureRequirement) -> bool:
        if not isinstance(requirement, CaptureRequirement):
            raise TypeError("requirement must be CaptureRequirement")
        return requirement in self.requirements


class CaptureUnavailableReason(str, Enum):
    """Why a conditional capture backend did not acquire a frame."""

    REQUIREMENT_UNMET = "requirement_unmet"
    SOURCE_UNAVAILABLE = "source_unavailable"
    PERMISSION_DENIED = "permission_denied"
    TRANSIENT_FAILURE = "transient_failure"


@dataclass(frozen=True, slots=True)
class CaptureUnavailable:
    """Typed non-exception result for an expected acquisition failure."""

    backend_id: str
    reason: CaptureUnavailableReason
    unmet_requirements: tuple[CaptureRequirement, ...] = ()
    detail: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.reason, CaptureUnavailableReason):
            raise TypeError("reason must be CaptureUnavailableReason")
        if not isinstance(self.unmet_requirements, tuple):
            raise TypeError("unmet_requirements must be a tuple")
        for requirement in self.unmet_requirements:
            if not isinstance(requirement, CaptureRequirement):
                raise TypeError(
                    "unmet_requirements must contain CaptureRequirement "
                    "values"
                )
        if len(set(self.unmet_requirements)) != len(
            self.unmet_requirements
        ):
            raise ValueError("unmet capture requirements cannot repeat")
        if self.reason is CaptureUnavailableReason.REQUIREMENT_UNMET:
            if not self.unmet_requirements:
                raise ValueError(
                    "requirement_unmet requires at least one unmet requirement"
                )
        elif self.unmet_requirements:
            raise ValueError(
                "unmet_requirements are only valid for requirement_unmet"
            )

        object.__setattr__(
            self,
            "backend_id",
            _normalize_non_empty_text(
                self.backend_id,
                field_name="capture backend id",
            ),
        )
        object.__setattr__(
            self,
            "detail",
            _normalize_optional_text(
                self.detail,
                field_name="capture unavailable detail",
            ),
        )
