from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePath
from urllib.parse import urlparse


def _normalize_text(value: object, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(
            f"{field_name} must be a string, "
            f"got {type(value).__name__}"
        )

    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} cannot be empty")

    return normalized


@dataclass(frozen=True, slots=True)
class FileLocator:
    path: str

    def __post_init__(self) -> None:
        path = _normalize_text(
            self.path,
            field_name="file locator path",
        )
        if PurePath(path).name in {"", ".", ".."}:
            raise ValueError("file locator path must identify a file")
        object.__setattr__(self, "path", path)


@dataclass(frozen=True, slots=True)
class HttpLocator:
    url: str

    def __post_init__(self) -> None:
        url = _normalize_text(
            self.url,
            field_name="HTTP locator URL",
        )
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError(
                "HTTP locator URL must be an absolute http or https URL"
            )
        object.__setattr__(self, "url", url)


@dataclass(frozen=True, slots=True)
class PackageLocator:
    package: str
    resource: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "package",
            _normalize_text(
                self.package,
                field_name="package locator package",
            ),
        )
        object.__setattr__(
            self,
            "resource",
            _normalize_text(
                self.resource,
                field_name="package locator resource",
            ),
        )


ReferenceAssetLocator = FileLocator | HttpLocator | PackageLocator
