from __future__ import annotations

from numbers import Integral

import cv2
import numpy as np

from geometry.rect import Rect
from vision.template_assets.domain.models import GrayImage, Template
from vision.template_matching.domain.results import MatchCandidate
from vision.template_matching.domain.scores import normalize_unit_score


class OpenCVTemplateMatchEngine:
    """
    OpenCV implementation of the TemplateMatchEngine port.

    The domain engine contract requires normalized scores in ``[0, 1]``
    where larger values always mean a better match. Therefore this adapter
    deliberately supports only OpenCV's normalized matching methods:

    - ``cv2.TM_CCORR_NORMED``
    - ``cv2.TM_CCOEFF_NORMED``
    - ``cv2.TM_SQDIFF_NORMED``

    ``TM_SQDIFF_NORMED`` is converted from a distance into a similarity by
    using ``1.0 - distance``. Negative correlation values produced by
    ``TM_CCOEFF_NORMED`` are clamped to ``0.0`` so the public score remains
    within the domain's unit-score range without changing positive
    correlation thresholds.

    OpenCV validity-mask support is intentionally restricted to
    ``TM_CCORR_NORMED``. Suppression, result limits, and business acceptance
    thresholds belong outside this adapter.
    """

    _SUPPORTED_METHODS = frozenset(
        {
            cv2.TM_CCORR_NORMED,
            cv2.TM_CCOEFF_NORMED,
            cv2.TM_SQDIFF_NORMED,
        }
    )
    _VALIDITY_MASK_SUPPORTED_METHODS = frozenset(
        {
            cv2.TM_CCORR_NORMED,
        }
    )
    _METHOD_NAMES = {
        cv2.TM_CCORR_NORMED: "TM_CCORR_NORMED",
        cv2.TM_CCOEFF_NORMED: "TM_CCOEFF_NORMED",
        cv2.TM_SQDIFF_NORMED: "TM_SQDIFF_NORMED",
    }

    def __init__(
        self,
        *,
        method: int = cv2.TM_CCORR_NORMED,
    ) -> None:
        self._method = self._normalize_method(method)

    @property
    def method(self) -> int:
        return self._method

    def match(
        self,
        image: GrayImage,
        template: Template,
        *,
        candidate_floor: float,
    ) -> tuple[MatchCandidate, ...]:
        self._validate_image(image)

        if not isinstance(template, Template):
            raise TypeError(
                "template must be Template, "
                f"got {type(template).__name__}"
            )

        normalized_floor = normalize_unit_score(
            candidate_floor,
            field_name="candidate_floor",
        )

        image_height, image_width = image.shape

        if (
            template.width > image_width
            or template.height > image_height
        ):
            return ()

        self._validate_validity_mask_support(template)

        image_input = np.ascontiguousarray(image)
        template_input = np.ascontiguousarray(template.gray)
        validity_mask_input = (
            None
            if template.validity_mask is None
            else np.ascontiguousarray(
                template.validity_mask
            )
        )

        try:
            if validity_mask_input is None:
                raw_scores = cv2.matchTemplate(
                    image_input,
                    template_input,
                    self._method,
                )
            else:
                raw_scores = cv2.matchTemplate(
                    image_input,
                    template_input,
                    self._method,
                    mask=validity_mask_input,
                )
        except cv2.error as exc:
            raise RuntimeError(
                "OpenCV template matching failed for "
                f"template {template.key!r} using "
                f"{self._method_name(self._method)}"
            ) from exc

        score_map = self._to_unit_similarity(raw_scores)
        finite_and_above_floor = (
            np.isfinite(score_map)
            & (score_map >= normalized_floor)
        )

        ys, xs = np.nonzero(finite_and_above_floor)

        return tuple(
            MatchCandidate(
                score=float(score_map[y, x]),
                rect=Rect(
                    x=int(x),
                    y=int(y),
                    width=template.width,
                    height=template.height,
                ),
            )
            for y, x in zip(ys, xs, strict=True)
        )

    def _to_unit_similarity(
        self,
        raw_scores: np.ndarray,
    ) -> np.ndarray:
        scores = np.asarray(raw_scores, dtype=np.float64)
        finite = np.isfinite(scores)

        if self._method == cv2.TM_SQDIFF_NORMED:
            normalized = 1.0 - np.clip(scores, 0.0, 1.0)
        else:
            normalized = np.clip(scores, 0.0, 1.0)

        # Keep OpenCV's NaN/Inf outputs from becoming valid candidates.
        return np.where(finite, normalized, np.nan)

    def _validate_validity_mask_support(
        self,
        template: Template,
    ) -> None:
        if template.validity_mask is None:
            return

        if self._method in self._VALIDITY_MASK_SUPPORTED_METHODS:
            return

        raise ValueError(
            "template validity masks are not supported with "
            f"{self._method_name(self._method)}; "
            "use TM_CCORR_NORMED or remove the validity mask"
        )

    @classmethod
    def _normalize_method(
        cls,
        method: object,
    ) -> int:
        if isinstance(method, bool) or not isinstance(method, Integral):
            raise TypeError(
                "OpenCV template matching method must be an integer, "
                f"got {type(method).__name__}"
            )

        normalized = int(method)

        if normalized not in cls._SUPPORTED_METHODS:
            supported = ", ".join(
                cls._method_name(value)
                for value in sorted(cls._SUPPORTED_METHODS)
            )
            raise ValueError(
                "unsupported OpenCV template matching method: "
                f"{normalized}; supported methods: {supported}"
            )

        return normalized

    @staticmethod
    def _validate_image(
        image: object,
    ) -> None:
        if not isinstance(image, np.ndarray):
            raise TypeError(
                "matching image must be a numpy array"
            )

        if image.dtype != np.uint8:
            raise TypeError(
                "matching image must be uint8, "
                f"got {image.dtype}"
            )

        if image.ndim != 2:
            raise ValueError(
                "matching image must be 2D grayscale, "
                f"got shape {image.shape}"
            )

        if image.size == 0:
            raise ValueError(
                "matching image cannot be empty"
            )

    @classmethod
    def _method_name(
        cls,
        method: int,
    ) -> str:
        return cls._METHOD_NAMES.get(
            method,
            f"method={method}",
        )
