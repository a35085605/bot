from __future__ import annotations

import hashlib
import unittest

import numpy as np

from template_assets.adapters.providers.in_memory import (
    InMemoryTemplateProvider,
)
from template_assets.application.resolver import TemplateResolver
from template_assets.domain.locators import FileLocator
from template_assets.domain.manifest import (
    TemplateManifestEntry,
    TemplateProvenance,
    TemplateStorageDefinition,
)
from template_assets.domain.models import Template
from template_matching.adapters.repositories.in_memory import (
    InMemoryTemplateRepository,
)
from template_matching.domain.models import Template as LegacyTemplate


class _ManifestRepository:
    def __init__(self, entry: TemplateManifestEntry) -> None:
        self._entry = entry

    def get(self, key: str) -> TemplateManifestEntry | None:
        return self._entry if key.strip() == self._entry.key else None

    def require(self, key: str) -> TemplateManifestEntry:
        entry = self.get(key)
        if entry is None:
            raise KeyError(key)
        return entry


class _ContentReader:
    def __init__(self, content: bytes) -> None:
        self._content = content

    def read(self, locator: object) -> bytes:
        return self._content


class _Decoder:
    def decode(
        self,
        *,
        key: str,
        content: bytes,
        mask_content: bytes | None = None,
    ) -> Template:
        return Template(
            key=key,
            gray=np.frombuffer(content, dtype=np.uint8).reshape(2, 2),
        )


class TemplateAssetsTest(unittest.TestCase):
    def test_template_owns_immutable_runtime_pixels(self) -> None:
        source = np.array([[1, 2], [3, 4]], dtype=np.uint8)
        template = Template(key=" submit ", gray=source)

        source[0, 0] = 99

        self.assertEqual(template.key, "submit")
        self.assertEqual(int(template.gray[0, 0]), 1)
        self.assertFalse(template.gray.flags.writeable)
        with self.assertRaises(ValueError):
            template.gray.setflags(write=True)

    def test_manifest_keeps_storage_and_provenance_outside_template(self) -> None:
        entry = TemplateManifestEntry(
            key="submit",
            storage=TemplateStorageDefinition(
                locator=FileLocator("assets/submit.png"),
                media_type="image/png",
            ),
            provenance=TemplateProvenance(
                source="login screen capture",
            ),
        )

        self.assertEqual(entry.key, "submit")
        self.assertEqual(entry.storage.locator.path, "assets/submit.png")
        self.assertEqual(entry.provenance.source, "login screen capture")

    def test_resolver_verifies_content_and_returns_template(self) -> None:
        content = bytes([1, 2, 3, 4])
        entry = TemplateManifestEntry(
            key="submit",
            storage=TemplateStorageDefinition(
                locator=FileLocator("assets/submit.raw"),
                sha256=hashlib.sha256(content).hexdigest(),
            ),
        )
        resolver = TemplateResolver(
            manifest_repository=_ManifestRepository(entry),
            content_reader=_ContentReader(content),
            decoder=_Decoder(),
        )

        template = resolver.require("submit")

        self.assertEqual(template.key, "submit")
        np.testing.assert_array_equal(
            template.gray,
            np.array([[1, 2], [3, 4]], dtype=np.uint8),
        )

    def test_legacy_imports_reference_new_asset_types(self) -> None:
        self.assertIs(LegacyTemplate, Template)
        self.assertIs(InMemoryTemplateRepository, InMemoryTemplateProvider)


if __name__ == "__main__":
    unittest.main()
