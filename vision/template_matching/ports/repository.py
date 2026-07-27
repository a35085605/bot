"""Compatibility alias for the provider moved to template_assets."""

from vision.template_assets.ports.provider import TemplateProvider

TemplateRepository = TemplateProvider

__all__ = [
    "TemplateProvider",
    "TemplateRepository",
]
