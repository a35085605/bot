from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import re

from template_assets.domain.keys import normalize_template_key
from template_assets.domain.locators import TemplateLocator


_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def _normalize_optional_text(
    value: object,
    *,
    field_name: str,
) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(
            f"{field_name} must be a string or None, "
            f"got {type(value).__name__}"
        )
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} cannot be empty")
    return normalized


@dataclass(frozen=True, slots=True)
class TemplateStorageDefinition:
    """Where encoded template content is stored and how it is verified."""

    locator: TemplateLocator
    sha256: str | None = None
    media_type: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(
            self.locator,
            TemplateLocator.__args__,
        ):
            raise TypeError(
                "storage locator must be a supported template locator"
            )

        digest = _normalize_optional_text(
            self.sha256,
            field_name="storage sha256",
        )
        if digest is not None:
            digest = digest.lower()
            if _SHA256_PATTERN.fullmatch(digest) is None:
                raise ValueError(
                    "storage sha256 must contain 64 hexadecimal characters"
                )

        media_type = _normalize_optional_text(
            self.media_type,
            field_name="storage media type",
        )

        object.__setattr__(self, "sha256", digest)
        object.__setattr__(self, "media_type", media_type)


@dataclass(frozen=True, slots=True)
class TemplateProvenance:
    """Human and system provenance for an asset, not matching policy."""

    source: str | None = None
    captured_at: datetime | None = None
    note: str | None = None

    def __post_init__(self) -> None:
        source = _normalize_optional_text(
            self.source,
            field_name="provenance source",
        )
        note = _normalize_optional_text(
            self.note,
            field_name="provenance note",
        )
        if self.captured_at is not None and not isinstance(
            self.captured_at,
            datetime,
        ):
            raise TypeError(
                "provenance captured_at must be datetime or None"
            )
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "note", note)


@dataclass(frozen=True, slots=True)
class TemplateManifestEntry:
    """Persistent asset definition resolved into a runtime Template."""

    key: str
    storage: TemplateStorageDefinition
    mask_storage: TemplateStorageDefinition | None = None
    provenance: TemplateProvenance = field(
        default_factory=TemplateProvenance
    )

    def __post_init__(self) -> None:
        key = normalize_template_key(self.key)
        if not isinstance(self.storage, TemplateStorageDefinition):
            raise TypeError(
                "manifest storage must be TemplateStorageDefinition"
            )
        if self.mask_storage is not None and not isinstance(
            self.mask_storage,
            TemplateStorageDefinition,
        ):
            raise TypeError(
                "manifest mask_storage must be "
                "TemplateStorageDefinition or None"
            )
        if not isinstance(self.provenance, TemplateProvenance):
            raise TypeError(
                "manifest provenance must be TemplateProvenance"
            )
        object.__setattr__(self, "key", key)
