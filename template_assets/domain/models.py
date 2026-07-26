from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypeAlias

import numpy as np
import numpy.typing as npt

from template_assets.domain.keys import normalize_template_key


GrayImage: TypeAlias = npt.NDArray[np.uint8]


def _freeze_gray_image(
    value: object,
    *,
    field_name: str,
    reject_all_zero: bool = False,
) -> GrayImage:
    """Validate and create an immutable, independently owned gray image."""
    if not isinstance(value, np.ndarray):
        raise TypeError(
            f"{field_name} must be a numpy array"
        )

    if value.dtype != np.uint8:
        raise TypeError(
            f"{field_name} must be uint8, got {value.dtype}"
        )

    if value.ndim != 2:
        raise ValueError(
            f"{field_name} must be 2D, got {value.shape}"
        )

    if value.size == 0:
        raise ValueError(
            f"{field_name} cannot be empty"
        )

    if reject_all_zero and not np.any(value):
        raise ValueError(
            f"{field_name} cannot be entirely zero"
        )

    return np.frombuffer(
        value.tobytes(order="C"),
        dtype=np.uint8,
    ).reshape(value.shape)


@dataclass(frozen=True, slots=True)
class Template:
    """
    Immutable runtime pixels for a stable logical template identity.

    A Template contains decoded image data only. Storage locators and
    provenance belong to TemplateManifestEntry, while matching policy belongs
    to the matching use case.
    """

    key: str
    gray: GrayImage = field(
        compare=False,
        hash=False,
        repr=False,
    )
    mask: GrayImage | None = field(
        default=None,
        compare=False,
        hash=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        key = normalize_template_key(self.key)
        gray = _freeze_gray_image(
            self.gray,
            field_name="template gray image",
        )
        mask: GrayImage | None = None

        if self.mask is not None:
            if not isinstance(self.mask, np.ndarray):
                raise TypeError(
                    "template mask must be a numpy array"
                )

            if self.mask.dtype != np.uint8:
                raise TypeError(
                    "template mask must be uint8, "
                    f"got {self.mask.dtype}"
                )

            if self.mask.ndim != 2:
                raise ValueError(
                    "template mask must be 2D, "
                    f"got {self.mask.shape}"
                )

            if self.mask.shape != gray.shape:
                raise ValueError(
                    "template mask shape must equal gray image shape"
                )

            mask = _freeze_gray_image(
                self.mask,
                field_name="template mask",
                reject_all_zero=True,
            )

        object.__setattr__(self, "key", key)
        object.__setattr__(self, "gray", gray)
        object.__setattr__(self, "mask", mask)

    @property
    def width(self) -> int:
        return int(self.gray.shape[1])

    @property
    def height(self) -> int:
        return int(self.gray.shape[0])
