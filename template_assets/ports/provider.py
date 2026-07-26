from __future__ import annotations

from typing import Protocol, Sequence

from template_assets.domain.models import Template


class TemplateProvider(Protocol):
    """Provide fully decoded immutable templates by stable key."""

    def get(self, key: str) -> Template | None:
        ...

    def require(self, key: str) -> Template:
        ...

    def require_many(
        self,
        keys: Sequence[str],
    ) -> list[Template]:
        ...
