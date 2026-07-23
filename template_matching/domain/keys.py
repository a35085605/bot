from __future__ import annotations


def normalize_template_key(
    value: object,
    *,
    field_name: str = "template key",
) -> str:
    """
    Validate and normalize a template key.

    Normalization rules:

    - value must be a string;
    - leading and trailing whitespace is removed;
    - the normalized key cannot be empty.
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
