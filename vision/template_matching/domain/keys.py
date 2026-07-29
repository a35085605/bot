from __future__ import annotations

from vision.reference_assets.domain.keys import (
    normalize_reference_asset_key,
)


def normalize_template_key(
    value: object,
    *,
    field_name: str = "template key",
) -> str:
    """Normalize the reference asset identity used for template matching."""

    return normalize_reference_asset_key(
        value,
        field_name=field_name,
    )


__all__ = [
    "normalize_template_key",
]
