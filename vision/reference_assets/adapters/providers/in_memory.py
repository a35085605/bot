from __future__ import annotations

from collections.abc import Iterable, Sequence

from vision.reference_assets.domain.keys import (
    normalize_reference_asset_key,
)
from vision.reference_assets.domain.models import ReferenceImage


class InMemoryReferenceAssetProvider:
    """Read-only provider indexed by stable reference asset key."""

    def __init__(
        self,
        assets: Iterable[ReferenceImage] = (),
    ) -> None:
        try:
            asset_items = tuple(assets)
        except TypeError as exc:
            raise TypeError("assets must be iterable") from exc

        assets_by_key: dict[str, ReferenceImage] = {}
        for index, asset in enumerate(asset_items):
            if not isinstance(asset, ReferenceImage):
                raise TypeError(
                    f"assets[{index}] must be ReferenceImage, "
                    f"got {type(asset).__name__}"
                )
            if asset.key in assets_by_key:
                raise ValueError(
                    "duplicate reference asset key: "
                    f"{asset.key!r}"
                )
            assets_by_key[asset.key] = asset

        self._assets = assets_by_key

    def get(self, key: str) -> ReferenceImage | None:
        return self._assets.get(
            normalize_reference_asset_key(key)
        )

    def require(self, key: str) -> ReferenceImage:
        normalized_key = normalize_reference_asset_key(key)
        try:
            return self._assets[normalized_key]
        except KeyError:
            raise KeyError(
                f"reference asset not found: {normalized_key!r}"
            ) from None

    def require_many(
        self,
        keys: Sequence[str],
    ) -> list[ReferenceImage]:
        if isinstance(keys, (str, bytes, bytearray)):
            raise TypeError(
                "reference asset keys must be a sequence of strings, "
                "not a single string"
            )
        if not isinstance(keys, Sequence):
            raise TypeError(
                "reference asset keys must be a sequence"
            )
        return [self.require(key) for key in keys]
