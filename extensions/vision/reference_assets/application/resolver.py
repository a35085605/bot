from __future__ import annotations

import hashlib
from collections.abc import Sequence

from extensions.vision.reference_assets.domain.manifest import (
    ReferenceAssetManifestEntry,
    ReferenceAssetStorageDefinition,
)
from extensions.vision.reference_assets.domain.models import ReferenceImage
from extensions.vision.reference_assets.domain.origins import (
    AssetRegionOrigin,
    ContentRegionOrigin,
    ExternalResourceOrigin,
    ReferenceAssetContentPlacement,
)
from extensions.vision.reference_assets.ports.content_reader import (
    ReferenceAssetContentReader,
)
from extensions.vision.reference_assets.ports.decoder import ReferenceAssetDecoder
from extensions.vision.reference_assets.ports.manifest_repository import (
    ReferenceAssetManifestRepository,
)


class ReferenceAssetResolver:
    """Resolve persistent definitions into detector-neutral images."""

    def __init__(
        self,
        manifest_repository: ReferenceAssetManifestRepository,
        content_reader: ReferenceAssetContentReader,
        decoder: ReferenceAssetDecoder,
    ) -> None:
        self._manifest_repository = manifest_repository
        self._content_reader = content_reader
        self._decoder = decoder

    def get(self, key: str) -> ReferenceImage | None:
        entry = self._manifest_repository.get(key)
        if entry is None:
            return None
        return self._resolve(entry)

    def require(self, key: str) -> ReferenceImage:
        return self._resolve(
            self._manifest_repository.require(key)
        )

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

    def _resolve(
        self,
        entry: ReferenceAssetManifestEntry,
    ) -> ReferenceImage:
        content = self._read_verified(entry.storage)
        coverage_mask_content = (
            None
            if entry.coverage_mask_storage is None
            else self._read_verified(
                entry.coverage_mask_storage
            )
        )

        asset = self._decoder.decode(
            key=entry.key,
            content=content,
            coverage_mask_content=coverage_mask_content,
        )
        if asset.key != entry.key:
            raise ValueError(
                "reference asset decoder returned an unexpected key: "
                f"expected={entry.key!r}, got={asset.key!r}"
            )

        origin = entry.origin
        if isinstance(
            origin,
            (ContentRegionOrigin, AssetRegionOrigin),
        ) and asset.image.size != origin.resolved_output_size:
            raise ValueError(
                "decoded reference asset size does not match origin "
                "output size: "
                f"expected={origin.resolved_output_size}, "
                f"got={asset.image.size}"
            )

        return asset

    def _read_verified(
        self,
        storage: ReferenceAssetStorageDefinition,
    ) -> bytes:
        content = self._content_reader.read(storage.locator)
        if not isinstance(content, bytes):
            raise TypeError(
                "reference asset content reader must return bytes, "
                f"got {type(content).__name__}"
            )

        if storage.sha256 is not None:
            actual = hashlib.sha256(content).hexdigest()
            if actual != storage.sha256:
                raise ValueError(
                    "reference asset content sha256 mismatch: "
                    f"expected={storage.sha256}, got={actual}"
                )

        return content


class ReferenceAssetLineageResolver:
    """Resolve nested asset-local origins into content-space."""

    def __init__(
        self,
        manifest_repository: ReferenceAssetManifestRepository,
    ) -> None:
        self._repository = manifest_repository

    def resolve_content_placement(
        self,
        key: str,
    ) -> ReferenceAssetContentPlacement | None:
        return self._resolve(key, stack=())

    def _resolve(
        self,
        key: str,
        *,
        stack: tuple[str, ...],
    ) -> ReferenceAssetContentPlacement | None:
        entry = self._repository.require(key)
        if entry.key in stack:
            chain = " -> ".join((*stack, entry.key))
            raise ValueError(
                "reference asset origin cycle detected: "
                f"{chain}"
            )

        origin = entry.origin
        if isinstance(origin, ExternalResourceOrigin):
            return None

        if isinstance(origin, ContentRegionOrigin):
            output_size = origin.resolved_output_size
            source = origin.source_bounds_content
            return ReferenceAssetContentPlacement(
                content=origin.content,
                asset_size=output_size,
                scale_x=source.width / output_size.width,
                scale_y=source.height / output_size.height,
                offset_x=float(source.x),
                offset_y=float(source.y),
            )

        parent_entry = self._repository.require(
            origin.parent_asset_key
        )
        if origin.expected_parent_sha256 is not None:
            actual_parent_sha256 = parent_entry.storage.sha256
            if actual_parent_sha256 != origin.expected_parent_sha256:
                raise ValueError(
                    "parent asset digest does not match nested origin: "
                    f"expected={origin.expected_parent_sha256}, "
                    f"got={actual_parent_sha256}"
                )

        parent = self._resolve(
            parent_entry.key,
            stack=(*stack, entry.key),
        )
        if parent is None:
            return None

        source = origin.source_bounds_parent
        if not (
            0 <= source.x
            and 0 <= source.y
            and source.right <= parent.asset_size.width
            and source.bottom <= parent.asset_size.height
        ):
            raise ValueError(
                f"asset source bounds for {entry.key!r} are outside "
                f"parent asset {origin.parent_asset_key!r}"
            )

        output_size = origin.resolved_output_size
        child_to_parent_scale_x = (
            source.width / output_size.width
        )
        child_to_parent_scale_y = (
            source.height / output_size.height
        )

        return ReferenceAssetContentPlacement(
            content=parent.content,
            asset_size=output_size,
            scale_x=(
                child_to_parent_scale_x * parent.scale_x
            ),
            scale_y=(
                child_to_parent_scale_y * parent.scale_y
            ),
            offset_x=(
                source.x * parent.scale_x + parent.offset_x
            ),
            offset_y=(
                source.y * parent.scale_y + parent.offset_y
            ),
        )
