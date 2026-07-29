from __future__ import annotations

import unittest

import numpy as np

from geometry.point import Point
from geometry.rect import Rect
from geometry.size import Size
from imaging import PixelFormat, RasterImage
from vision.reference_assets import (
    AssetRegionOrigin,
    ContentRegionOrigin,
    ExternalResourceOrigin,
    FileLocator,
    ReferenceAssetLineageResolver,
    ReferenceAssetManifestEntry,
    ReferenceAssetStorageDefinition,
    ReferenceContentProfile,
    ReferenceImage,
)
from vision.reference_assets.adapters.providers.in_memory import (
    InMemoryReferenceAssetProvider,
)
from vision.template_matching.application.matching_service import (
    TemplateMatchingService,
)
from vision.template_matching.application.template_factory import (
    ReferenceMatchTemplateFactory,
)
from vision.template_matching.domain.models import MatchTemplate
from vision.template_matching.domain.results import MatchCandidate


class _ManifestRepository:
    def __init__(
        self,
        *entries: ReferenceAssetManifestEntry,
    ) -> None:
        self._entries = {
            entry.key: entry
            for entry in entries
        }

    def get(
        self,
        key: str,
    ) -> ReferenceAssetManifestEntry | None:
        return self._entries.get(key.strip())

    def require(self, key: str) -> ReferenceAssetManifestEntry:
        entry = self.get(key)
        if entry is None:
            raise KeyError(key)
        return entry


class _RecordingEngine:
    def __init__(self) -> None:
        self.template: MatchTemplate | None = None

    def match(
        self,
        image: np.ndarray,
        template: MatchTemplate,
        *,
        candidate_floor: float,
    ) -> tuple[MatchCandidate, ...]:
        self.template = template
        return (
            MatchCandidate(
                score=0.9,
                rect=Rect(
                    x=1,
                    y=1,
                    width=template.width,
                    height=template.height,
                ),
            ),
        )


class _IdentitySuppression:
    def suppress(
        self,
        candidates: tuple[MatchCandidate, ...],
    ) -> tuple[MatchCandidate, ...]:
        return tuple(candidates)


class ReferenceAssetsTest(unittest.TestCase):
    def test_nested_asset_local_origin_resolves_to_content(self) -> None:
        profile = ReferenceContentProfile(
            key="game.main.1920x1080",
            size=Size(width=1920, height=1080),
            pixel_format=PixelFormat.BGRA32,
        )
        homepage = ReferenceAssetManifestEntry(
            key="scene.homepage",
            storage=ReferenceAssetStorageDefinition(
                locator=FileLocator("assets/homepage.png"),
            ),
            origin=ContentRegionOrigin(
                content=profile,
                source_bounds_content=Rect(
                    x=100,
                    y=50,
                    width=1600,
                    height=900,
                ),
                output_size=Size(width=800, height=450),
            ),
        )
        store_button = ReferenceAssetManifestEntry(
            key="control.store_button",
            storage=ReferenceAssetStorageDefinition(
                locator=FileLocator("assets/store-button.png"),
            ),
            origin=AssetRegionOrigin(
                parent_asset_key="scene.homepage",
                source_bounds_parent=Rect(
                    x=700,
                    y=20,
                    width=80,
                    height=40,
                ),
                output_size=Size(width=160, height=80),
            ),
        )

        placement = ReferenceAssetLineageResolver(
            _ManifestRepository(homepage, store_button)
        ).resolve_content_placement("control.store_button")

        self.assertIsNotNone(placement)
        assert placement is not None
        self.assertEqual(
            placement.asset_size,
            Size(width=160, height=80),
        )
        self.assertEqual(
            placement.point_to_content(Point(x=0, y=0)),
            Point(x=1500, y=90),
        )
        self.assertEqual(
            placement.rect_to_content(
                Rect(x=0, y=0, width=160, height=80)
            ),
            Rect(x=1500, y=90, width=160, height=80),
        )

    def test_external_resource_has_no_content_placement(self) -> None:
        asset = ReferenceAssetManifestEntry(
            key="control.store_button",
            storage=ReferenceAssetStorageDefinition(
                locator=FileLocator("assets/store-button.png"),
            ),
            origin=ExternalResourceOrigin(
                locator=FileLocator("game/ui.bundle"),
                member="sprites/store_button",
                decoder_id="unity.sprite.v1",
            ),
        )

        placement = ReferenceAssetLineageResolver(
            _ManifestRepository(asset)
        ).resolve_content_placement("control.store_button")

        self.assertIsNone(placement)

    def test_reference_image_can_preserve_color_pixels(self) -> None:
        asset = ReferenceImage(
            key="palette.primary",
            image=RasterImage(
                pixels=np.ones((2, 3, 3), dtype=np.uint8),
                pixel_format=PixelFormat.BGR24,
            ),
        )

        self.assertEqual(asset.image.channel_count, 3)
        with self.assertRaises(ValueError):
            ReferenceMatchTemplateFactory().create(asset)

    def test_match_template_has_no_asset_identity(self) -> None:
        asset = ReferenceImage(
            key="control.store_button",
            image=RasterImage(
                pixels=np.ones((2, 3), dtype=np.uint8),
                pixel_format=PixelFormat.GRAY8,
            ),
            coverage_mask=np.array(
                [
                    [0, 1, 1],
                    [1, 1, 1],
                ],
                dtype=np.uint8,
            ),
        )

        template = ReferenceMatchTemplateFactory().create(asset)

        self.assertIsInstance(template, MatchTemplate)
        self.assertFalse(hasattr(template, "key"))
        self.assertEqual(template.gray.shape, (2, 3))
        self.assertEqual(int(template.mask[0, 1]), 255)

    def test_matching_service_keeps_identity_outside_engine(self) -> None:
        asset = ReferenceImage(
            key="control.store_button",
            image=RasterImage(
                pixels=np.ones((2, 2), dtype=np.uint8),
                pixel_format=PixelFormat.GRAY8,
            ),
        )
        engine = _RecordingEngine()
        service = TemplateMatchingService(
            repository=InMemoryReferenceAssetProvider((asset,)),
            engine=engine,
            suppression=_IdentitySuppression(),
        )

        result = service.match(
            image=np.ones((5, 5), dtype=np.uint8),
            template_key="control.store_button",
            candidate_floor=0.5,
        )

        self.assertIsInstance(engine.template, MatchTemplate)
        assert engine.template is not None
        self.assertFalse(hasattr(engine.template, "key"))
        self.assertEqual(result.template_key, asset.key)


if __name__ == "__main__":
    unittest.main()
