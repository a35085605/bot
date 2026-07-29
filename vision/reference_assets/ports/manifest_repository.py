from __future__ import annotations

from typing import Protocol

from vision.reference_assets.domain.manifest import (
    ReferenceAssetManifestEntry,
)


class ReferenceAssetManifestRepository(Protocol):
    def get(
        self,
        key: str,
    ) -> ReferenceAssetManifestEntry | None:
        ...

    def require(self, key: str) -> ReferenceAssetManifestEntry:
        ...
