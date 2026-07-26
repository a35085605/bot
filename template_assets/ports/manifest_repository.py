from __future__ import annotations

from typing import Protocol

from template_assets.domain.manifest import TemplateManifestEntry


class TemplateManifestRepository(Protocol):
    def get(self, key: str) -> TemplateManifestEntry | None:
        ...

    def require(self, key: str) -> TemplateManifestEntry:
        ...
