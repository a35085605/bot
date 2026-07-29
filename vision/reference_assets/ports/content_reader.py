from __future__ import annotations

from typing import Protocol

from vision.reference_assets.domain.locators import ReferenceAssetLocator


class ReferenceAssetContentReader(Protocol):
    def read(self, locator: ReferenceAssetLocator) -> bytes:
        ...
