from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import re

from extensions.vision.reference_assets.domain.keys import (
    normalize_reference_asset_key,
)
from extensions.vision.reference_assets.domain.locators import (
    FileLocator,
    HttpLocator,
    PackageLocator,
    ReferenceAssetLocator,
)
from extensions.vision.reference_assets.domain.origins import (
    AssetRegionOrigin,
    ContentRegionOrigin,
    ExternalResourceOrigin,
    ReferenceAssetOrigin,
)


_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_LOCATOR_TYPES = (
    FileLocator,
    HttpLocator,
    PackageLocator,
)
_ORIGIN_TYPES = (
    ContentRegionOrigin,
    AssetRegionOrigin,
    ExternalResourceOrigin,
)


def _normalize_optional_text(
    value: object,
    *,
    field_name: str,
) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string or None")

    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} cannot be empty")
    return normalized


@dataclass(frozen=True, slots=True)
class ReferenceAssetStorageDefinition:
    """Where materialized reference asset content is stored."""

    locator: ReferenceAssetLocator
    sha256: str | None = None
    media_type: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.locator, _LOCATOR_TYPES):
            raise TypeError(
                "storage locator must be a supported reference asset "
                "locator"
            )

        digest = _normalize_optional_text(
            self.sha256,
            field_name="storage sha256",
        )
        if digest is not None:
            digest = digest.lower()
            if _SHA256_PATTERN.fullmatch(digest) is None:
                raise ValueError(
                    "storage sha256 must contain 64 hexadecimal "
                    "characters"
                )

        object.__setattr__(self, "sha256", digest)
        object.__setattr__(
            self,
            "media_type",
            _normalize_optional_text(
                self.media_type,
                field_name="storage media type",
            ),
        )


@dataclass(frozen=True, slots=True)
class ReferenceAssetProvenance:
    """Authoring metadata separate from source lineage."""

    authored_at: datetime | None = None
    authoring_tool: str | None = None
    note: str | None = None

    def __post_init__(self) -> None:
        if self.authored_at is not None and not isinstance(
            self.authored_at,
            datetime,
        ):
            raise TypeError("authored_at must be datetime or None")

        object.__setattr__(
            self,
            "authoring_tool",
            _normalize_optional_text(
                self.authoring_tool,
                field_name="authoring tool",
            ),
        )
        object.__setattr__(
            self,
            "note",
            _normalize_optional_text(
                self.note,
                field_name="provenance note",
            ),
        )


@dataclass(frozen=True, slots=True)
class ReferenceAssetManifestEntry:
    """Persistent asset definition resolved into a ReferenceImage."""

    key: str
    storage: ReferenceAssetStorageDefinition
    origin: ReferenceAssetOrigin
    coverage_mask_storage: ReferenceAssetStorageDefinition | None = None
    provenance: ReferenceAssetProvenance = field(
        default_factory=ReferenceAssetProvenance
    )

    def __post_init__(self) -> None:
        if not isinstance(
            self.storage,
            ReferenceAssetStorageDefinition,
        ):
            raise TypeError(
                "storage must be ReferenceAssetStorageDefinition"
            )
        if not isinstance(self.origin, _ORIGIN_TYPES):
            raise TypeError(
                "origin must be a supported ReferenceAssetOrigin"
            )
        if self.coverage_mask_storage is not None and not isinstance(
            self.coverage_mask_storage,
            ReferenceAssetStorageDefinition,
        ):
            raise TypeError(
                "coverage_mask_storage must be "
                "ReferenceAssetStorageDefinition or None"
            )
        if not isinstance(
            self.provenance,
            ReferenceAssetProvenance,
        ):
            raise TypeError(
                "provenance must be ReferenceAssetProvenance"
            )

        object.__setattr__(
            self,
            "key",
            normalize_reference_asset_key(self.key),
        )
