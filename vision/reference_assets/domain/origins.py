from __future__ import annotations

from dataclasses import dataclass
import math
import re

from geometry.point import Point
from geometry.rect import Rect
from geometry.size import Size
from vision.reference_assets.domain.keys import (
    normalize_reference_asset_key,
)
from vision.reference_assets.domain.locators import (
    FileLocator,
    HttpLocator,
    PackageLocator,
    ReferenceAssetLocator,
)
from vision.reference_assets.domain.models import ReferenceImageFormat


_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_LOCATOR_TYPES = (
    FileLocator,
    HttpLocator,
    PackageLocator,
)


def _normalize_optional_text(
    value: object,
    *,
    field_name: str,
) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string or None")

    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} cannot be empty")
    return normalized


def _normalize_optional_sha256(
    value: object,
    *,
    field_name: str,
) -> str | None:
    normalized = _normalize_optional_text(
        value,
        field_name=field_name,
    )
    if normalized is None:
        return None

    normalized = normalized.lower()
    if _SHA256_PATTERN.fullmatch(normalized) is None:
        raise ValueError(
            f"{field_name} must contain 64 hexadecimal characters"
        )
    return normalized


@dataclass(frozen=True, slots=True)
class ReferenceContentProfile:
    """Stable authoring-time content coordinate space."""

    key: str
    size: Size
    pixel_format: ReferenceImageFormat

    def __post_init__(self) -> None:
        if not isinstance(self.size, Size):
            raise TypeError("content profile size must be Size")
        if not isinstance(self.pixel_format, ReferenceImageFormat):
            raise TypeError(
                "content profile pixel_format must be "
                "ReferenceImageFormat"
            )
        object.__setattr__(
            self,
            "key",
            normalize_reference_asset_key(
                self.key,
                field_name="content profile key",
            ),
        )


@dataclass(frozen=True, slots=True)
class ContentRegionOrigin:
    """Asset derived from one region in a reference content profile."""

    content: ReferenceContentProfile
    source_bounds_content: Rect
    output_size: Size | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.content, ReferenceContentProfile):
            raise TypeError(
                "content must be ReferenceContentProfile"
            )
        if not isinstance(self.source_bounds_content, Rect):
            raise TypeError("source_bounds_content must be Rect")
        if self.output_size is not None and not isinstance(
            self.output_size,
            Size,
        ):
            raise TypeError("output_size must be Size or None")

        content_bounds = Rect(
            x=0,
            y=0,
            width=self.content.size.width,
            height=self.content.size.height,
        )
        if not content_bounds.contains_rect(
            self.source_bounds_content
        ):
            raise ValueError(
                "content source bounds must be inside reference content"
            )

    @property
    def resolved_output_size(self) -> Size:
        if self.output_size is not None:
            return self.output_size
        return Size(
            width=self.source_bounds_content.width,
            height=self.source_bounds_content.height,
        )


@dataclass(frozen=True, slots=True)
class AssetRegionOrigin:
    """Asset derived from a parent asset-local region."""

    parent_asset_key: str
    source_bounds_parent: Rect
    output_size: Size | None = None
    expected_parent_sha256: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.source_bounds_parent, Rect):
            raise TypeError("source_bounds_parent must be Rect")
        if self.output_size is not None and not isinstance(
            self.output_size,
            Size,
        ):
            raise TypeError("output_size must be Size or None")

        object.__setattr__(
            self,
            "parent_asset_key",
            normalize_reference_asset_key(
                self.parent_asset_key,
                field_name="parent asset key",
            ),
        )
        object.__setattr__(
            self,
            "expected_parent_sha256",
            _normalize_optional_sha256(
                self.expected_parent_sha256,
                field_name="expected parent sha256",
            ),
        )

    @property
    def resolved_output_size(self) -> Size:
        if self.output_size is not None:
            return self.output_size
        return Size(
            width=self.source_bounds_parent.width,
            height=self.source_bounds_parent.height,
        )


@dataclass(frozen=True, slots=True)
class ExternalResourceOrigin:
    """Asset derived from a non-capture external resource."""

    locator: ReferenceAssetLocator
    member: str | None = None
    decoder_id: str | None = None
    source_sha256: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.locator, _LOCATOR_TYPES):
            raise TypeError(
                "origin locator must be a supported reference asset "
                "locator"
            )
        object.__setattr__(
            self,
            "member",
            _normalize_optional_text(
                self.member,
                field_name="origin member",
            ),
        )
        object.__setattr__(
            self,
            "decoder_id",
            _normalize_optional_text(
                self.decoder_id,
                field_name="origin decoder id",
            ),
        )
        object.__setattr__(
            self,
            "source_sha256",
            _normalize_optional_sha256(
                self.source_sha256,
                field_name="origin source sha256",
            ),
        )


ReferenceAssetOrigin = (
    ContentRegionOrigin
    | AssetRegionOrigin
    | ExternalResourceOrigin
)


@dataclass(frozen=True, slots=True)
class ReferenceAssetContentPlacement:
    """Axis-aligned asset-local to reference-content placement."""

    content: ReferenceContentProfile
    asset_size: Size
    scale_x: float
    scale_y: float
    offset_x: float
    offset_y: float

    def point_to_content(self, point: Point) -> Point:
        if not isinstance(point, Point):
            raise TypeError("point must be Point")
        if not (
            0 <= point.x < self.asset_size.width
            and 0 <= point.y < self.asset_size.height
        ):
            raise ValueError("point must be inside asset bounds")

        return Point(
            x=int(round(point.x * self.scale_x + self.offset_x)),
            y=int(round(point.y * self.scale_y + self.offset_y)),
        )

    def rect_to_content(self, rect: Rect) -> Rect:
        if not isinstance(rect, Rect):
            raise TypeError("rect must be Rect")

        asset_bounds = Rect(
            x=0,
            y=0,
            width=self.asset_size.width,
            height=self.asset_size.height,
        )
        if not asset_bounds.contains_rect(rect):
            raise ValueError("rect must be inside asset bounds")

        return Rect.from_ltrb(
            left=math.floor(
                rect.left * self.scale_x + self.offset_x
            ),
            top=math.floor(
                rect.top * self.scale_y + self.offset_y
            ),
            right=math.ceil(
                rect.right * self.scale_x + self.offset_x
            ),
            bottom=math.ceil(
                rect.bottom * self.scale_y + self.offset_y
            ),
        )
