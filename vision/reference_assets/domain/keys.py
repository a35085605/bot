from __future__ import annotations


def normalize_reference_asset_key(
    value: object,
    *,
    field_name: str = "reference asset key",
) -> str:
    """Validate and normalize a stable logical reference asset identity."""
    if not isinstance(value, str):
        raise TypeError(
            f"{field_name} must be a string, "
            f"got {type(value).__name__}"
        )

    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} cannot be empty")

    return normalized
