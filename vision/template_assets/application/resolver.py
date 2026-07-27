from __future__ import annotations

import hashlib
from typing import Sequence

from vision.template_assets.domain.manifest import (
    TemplateManifestEntry,
    TemplateStorageDefinition,
)
from vision.template_assets.domain.models import Template
from vision.template_assets.ports.content_reader import TemplateContentReader
from vision.template_assets.ports.decoder import TemplateDecoder
from vision.template_assets.ports.manifest_repository import (
    TemplateManifestRepository,
)


class TemplateResolver:
    """Resolve manifest definitions into immutable runtime templates."""

    def __init__(
        self,
        manifest_repository: TemplateManifestRepository,
        content_reader: TemplateContentReader,
        decoder: TemplateDecoder,
    ) -> None:
        self._manifest_repository = manifest_repository
        self._content_reader = content_reader
        self._decoder = decoder

    def get(self, key: str) -> Template | None:
        entry = self._manifest_repository.get(key)
        if entry is None:
            return None
        return self._resolve(entry)

    def require(self, key: str) -> Template:
        return self._resolve(
            self._manifest_repository.require(key)
        )

    def require_many(
        self,
        keys: Sequence[str],
    ) -> list[Template]:
        if isinstance(keys, (str, bytes, bytearray)):
            raise TypeError(
                "template keys must be a sequence of strings, "
                "not a single string"
            )
        if not isinstance(keys, Sequence):
            raise TypeError("template keys must be a sequence")
        return [self.require(key) for key in keys]

    def _resolve(
        self,
        entry: TemplateManifestEntry,
    ) -> Template:
        content = self._read_verified(entry.storage)
        validity_mask_content = (
            None
            if entry.validity_mask_storage is None
            else self._read_verified(
                entry.validity_mask_storage
            )
        )
        template = self._decoder.decode(
            key=entry.key,
            content=content,
            validity_mask_content=validity_mask_content,
        )
        if template.key != entry.key:
            raise ValueError(
                "template decoder returned an unexpected key: "
                f"expected={entry.key!r}, got={template.key!r}"
            )
        return template

    def _read_verified(
        self,
        storage: TemplateStorageDefinition,
    ) -> bytes:
        content = self._content_reader.read(storage.locator)
        if not isinstance(content, bytes):
            raise TypeError(
                "template content reader must return bytes, "
                f"got {type(content).__name__}"
            )

        if storage.sha256 is not None:
            actual = hashlib.sha256(content).hexdigest()
            if actual != storage.sha256:
                raise ValueError(
                    "template content sha256 mismatch: "
                    f"expected={storage.sha256}, got={actual}"
                )

        return content
