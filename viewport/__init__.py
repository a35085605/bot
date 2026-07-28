"""Deprecated viewport compatibility exports.

New code should import clean-content models from :mod:`content`.
"""

from viewport.models import (
    CanonicalViewport,
    ContentPlacement,
    ViewportPlacement,
)

__all__ = [
    "CanonicalViewport",
    "ContentPlacement",
    "ViewportPlacement",
]
