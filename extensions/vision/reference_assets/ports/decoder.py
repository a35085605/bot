from __future__ import annotations

from typing import Protocol

from extensions.vision.reference_assets.domain.models import ReferenceImage


class ReferenceAssetDecoder(Protocol):
    """Decode materialized bytes into a detector-neutral image."""

    def decode(
        self,
        *,
        key: str,
        content: bytes,
        coverage_mask_content: bytes | None = None,
    ) -> ReferenceImage:
        ...
