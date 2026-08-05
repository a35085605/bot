from __future__ import annotations

from typing import Protocol, Sequence

from extensions.vision.reference_assets.domain.models import ReferenceImage


class ReferenceAssetProvider(Protocol):
    """Provide decoded immutable reference images by stable key."""

    def get(self, key: str) -> ReferenceImage | None:
        ...

    def require(self, key: str) -> ReferenceImage:
        ...

    def require_many(
        self,
        keys: Sequence[str],
    ) -> list[ReferenceImage]:
        ...
