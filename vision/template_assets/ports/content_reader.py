from __future__ import annotations

from typing import Protocol

from vision.template_assets.domain.locators import TemplateLocator


class TemplateContentReader(Protocol):
    """Read encoded asset bytes from a replaceable locator."""

    def read(self, locator: TemplateLocator) -> bytes:
        ...
