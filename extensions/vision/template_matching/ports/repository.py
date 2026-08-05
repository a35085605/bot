"""Compatibility names for the reference asset provider port."""

from extensions.vision.reference_assets.ports.provider import ReferenceAssetProvider


TemplateProvider = ReferenceAssetProvider
TemplateRepository = ReferenceAssetProvider


__all__ = [
    "ReferenceAssetProvider",
    "TemplateProvider",
    "TemplateRepository",
]
