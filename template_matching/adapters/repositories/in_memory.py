"""Compatibility alias for the provider moved to template_assets."""

from template_assets.adapters.providers.in_memory import (
    InMemoryTemplateProvider,
)

InMemoryTemplateRepository = InMemoryTemplateProvider

__all__ = [
    "InMemoryTemplateProvider",
    "InMemoryTemplateRepository",
]
