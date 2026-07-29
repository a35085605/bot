from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import numpy.typing as npt


GrayImage = npt.NDArray[np.uint8]
ValidityMask = npt.NDArray[np.uint8]


def _freeze_gray_image(
    value: object,
    *,
    field_name: str,
    reject_all_zero: bool = False,
) -> GrayImage:
    if not isinstance(value, np.ndarray):
        raise TypeError(f"{field_name} must be a numpy array")
    if value.dtype != np.uint8:
        raise TypeError(
            f"{field_name} must be uint8, got {value.dtype}"
        )
    if value.ndim != 2:
        raise ValueError(
            f"{field_name} must be 2D, got {value.shape}"
        )
    if value.size == 0:
        raise ValueError(f"{field_name} cannot be empty")
    if reject_all_zero and not np.any(value):
        raise ValueError(f"{field_name} cannot be entirely zero")

    return np.frombuffer(
        value.tobytes(order="C"),
        dtype=np.uint8,
    ).reshape(value.shape)


@dataclass(frozen=True, slots=True)
class MatchTemplate:
    """Detector-local matching pixels without asset metadata."""

    gray: GrayImage = field(
        compare=False,
        hash=False,
        repr=False,
    )
    mask: ValidityMask | None = field(
        default=None,
        compare=False,
        hash=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        gray = _freeze_gray_image(
            self.gray,
            field_name="match template gray image",
        )
        mask = None

        if self.mask is not None:
            if not isinstance(self.mask, np.ndarray):
                raise TypeError(
                    "match template mask must be a numpy array"
                )
            if self.mask.dtype != np.uint8:
                raise TypeError(
                    "match template mask must be uint8, "
                    f"got {self.mask.dtype}"
                )
            if self.mask.ndim != 2:
                raise ValueError(
                    "match template mask must be 2D, "
                    f"got {self.mask.shape}"
                )
            if self.mask.shape != gray.shape:
                raise ValueError(
                    "match template mask shape must equal gray image "
                    "shape"
                )

            binary = np.where(
                self.mask != 0,
                255,
                0,
            ).astype(np.uint8, copy=False)
            mask = _freeze_gray_image(
                binary,
                field_name="match template mask",
                reject_all_zero=True,
            )

        object.__setattr__(self, "gray", gray)
        object.__setattr__(self, "mask", mask)

    @property
    def width(self) -> int:
        return int(self.gray.shape[1])

    @property
    def height(self) -> int:
        return int(self.gray.shape[0])


__all__ = [
    "GrayImage",
    "MatchTemplate",
    "ValidityMask",
]
