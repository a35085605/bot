"""Compatibility names for the reference asset provider."""

from vision.reference_assets.adapters.providers.in_memory import (
    InMemoryReferenceAssetProvider,
)


InMemoryTemplateProvider = InMemoryReferenceAssetProvider
InMemoryTemplateRepository = InMemoryReferenceAssetProvider


__all__ = [
    "InMemoryReferenceAssetProvider",
    "InMemoryTemplateProvider",
    "InMemoryTemplateRepository",
]
