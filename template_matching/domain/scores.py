from __future__ import annotations

import math
from numbers import Real


def normalize_unit_score(
    value: float,
    *,
    field_name: str,
) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(
            f"{field_name} must be a real number, "
            f"got {type(value).__name__}"
        )

    normalized = float(value)

    if not math.isfinite(normalized):
        raise ValueError(
            f"{field_name} must be finite"
        )

    if not 0.0 <= normalized <= 1.0:
        raise ValueError(
            f"{field_name} must be between 0 and 1, "
            f"got {normalized}"
        )

    return normalized
