from __future__ import annotations


def normalize_template_key(
    value: object,
    *,
    field_name: str = "template key",
) -> str:
    """
    Validate and normalize a stable logical template identity.

    Storage paths and URLs are deliberately not part of the key. They are
    replaceable locators described by a template manifest.
    """
    if not isinstance(value, str):
        raise TypeError(
            f"{field_name} must be a string, "
            f"got {type(value).__name__}"
        )

    normalized = value.strip()

    if not normalized:
        raise ValueError(
            f"{field_name} cannot be empty"
        )

    return normalized
