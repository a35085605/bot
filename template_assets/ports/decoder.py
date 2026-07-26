from __future__ import annotations

from typing import Protocol

from template_assets.domain.models import Template


class TemplateDecoder(Protocol):
    """Decode encoded content into immutable runtime pixels."""

    def decode(
        self,
        *,
        key: str,
        content: bytes,
        validity_mask_content: bytes | None = None,
    ) -> Template:
        ...
