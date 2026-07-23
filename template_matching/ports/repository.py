from __future__ import annotations

from typing import Protocol, Sequence

from template_matching.domain.models import Template


class TemplateRepository(Protocol):
    def get(self, key: str) -> Template | None:
        ...

    def require(self, key: str) -> Template:
        ...

    def require_many(
        self,
        keys: Sequence[str],
    ) -> list[Template]:
        ...
