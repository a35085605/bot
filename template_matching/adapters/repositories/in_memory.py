from __future__ import annotations

from collections.abc import Iterable, Sequence

from template_matching.domain.models import Template
from template_matching.domain.keys import normalize_template_key


class InMemoryTemplateRepository:
    """
    Read-only in-memory implementation of TemplateRepository.

    Templates are indexed by their normalized domain key.
    Duplicate keys are rejected during construction to prevent
    accidental silent replacement.
    """

    def __init__(
        self,
        templates: Iterable[Template] = (),
    ) -> None:
        try:
            template_items = tuple(templates)
        except TypeError as exc:
            raise TypeError(
                "templates must be iterable"
            ) from exc

        templates_by_key: dict[str, Template] = {}

        for index, template in enumerate(template_items):
            if not isinstance(template, Template):
                raise TypeError(
                    f"templates[{index}] must be Template, "
                    f"got {type(template).__name__}"
                )

            if template.key in templates_by_key:
                raise ValueError(
                    "duplicate template key: "
                    f"{template.key!r}"
                )

            templates_by_key[template.key] = template

        self._templates = templates_by_key

    def get(
        self,
        key: str,
    ) -> Template | None:
        normalized_key = normalize_template_key(key)
        return self._templates.get(normalized_key)

    def require(
        self,
        key: str,
    ) -> Template:
        normalized_key = normalize_template_key(key)

        try:
            return self._templates[normalized_key]
        except KeyError:
            raise KeyError(
                f"template not found: {normalized_key!r}"
            ) from None

    def require_many(
        self,
        keys: Sequence[str],
    ) -> list[Template]:
        if isinstance(keys, (str, bytes, bytearray)):
            raise TypeError(
                "template keys must be a sequence of strings, "
                "not a single string"
            )

        if not isinstance(keys, Sequence):
            raise TypeError(
                "template keys must be a sequence"
            )

        normalized_keys = tuple(
            normalize_template_key(key)
            for key in keys
        )

        missing_keys = tuple(
            dict.fromkeys(
                key
                for key in normalized_keys
                if key not in self._templates
            )
        )

        if missing_keys:
            formatted_keys = ", ".join(
                repr(key)
                for key in missing_keys
            )

            raise KeyError(
                f"templates not found: {formatted_keys}"
            )

        return [
            self._templates[key]
            for key in normalized_keys
        ]
