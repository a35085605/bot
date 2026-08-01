from __future__ import annotations

from datetime import datetime, timezone
import unittest

import numpy as np

from geometry.rect import Rect
from imaging import RasterImage, crop_image
from observation.capture import (
    AcquiredFrame,
    CapturedFrame,
    CaptureBackendProfile,
    CaptureQuality,
    CaptureRequirement,
    CaptureStreamId,
    CaptureUnavailable,
    CaptureUnavailableReason,
    CoordinateSpace,
    CoordinateTransform,
    FrameId,
    FrameInfo,
    MaterializingFrameSource,
    PixelFormat,
)


class CaptureRequirementsTest(unittest.TestCase):
    def _frame_info(self) -> FrameInfo:
        return FrameInfo(
            frame_id=FrameId(1),
            stream_id=CaptureStreamId("session-1"),
            captured_at=datetime.now(timezone.utc),
            root_bounds=Rect(x=0, y=0, width=4, height=3),
            source_id="game-window",
            surface=None,
            root_to_screen=CoordinateTransform(
                source=CoordinateSpace.ROOT,
                target=CoordinateSpace.SCREEN,
            ),
            capture_backend_id="desktop.copy",
        )

    def test_backend_profile_declares_capture_specific_requirements(self) -> None:
        profile = CaptureBackendProfile(
            backend_id=" desktop.copy ",
            requirements=frozenset(
                {
                    CaptureRequirement.WINDOW_FOREGROUND,
                    CaptureRequirement.WINDOW_UNOBSCURED,
                }
            ),
        )

        self.assertEqual(profile.backend_id, "desktop.copy")
        self.assertTrue(
            profile.requires(CaptureRequirement.WINDOW_FOREGROUND)
        )
        self.assertFalse(
            profile.requires(CaptureRequirement.ADB_TRANSPORT_READY)
        )

    def test_requirement_unmet_requires_typed_requirements(self) -> None:
        unavailable = CaptureUnavailable(
            backend_id="desktop.copy",
            reason=CaptureUnavailableReason.REQUIREMENT_UNMET,
            unmet_requirements=(CaptureRequirement.WINDOW_FOREGROUND,),
            detail=" target window is not foreground ",
        )

        self.assertEqual(
            unavailable.unmet_requirements,
            (CaptureRequirement.WINDOW_FOREGROUND,),
        )
        self.assertEqual(
            unavailable.detail,
            "target window is not foreground",
        )

        with self.assertRaisesRegex(
            ValueError,
            "requires at least one unmet requirement",
        ):
            CaptureUnavailable(
                backend_id="desktop.copy",
                reason=CaptureUnavailableReason.REQUIREMENT_UNMET,
            )

    def test_non_requirement_failure_rejects_unmet_requirements(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "only valid for requirement_unmet",
        ):
            CaptureUnavailable(
                backend_id="desktop.copy",
                reason=CaptureUnavailableReason.PERMISSION_DENIED,
                unmet_requirements=(
                    CaptureRequirement.WINDOW_FOREGROUND,
                ),
            )

    def test_frame_source_materializes_successful_acquisition(self) -> None:
        root = RasterImage(
            pixels=np.arange(5 * 6, dtype=np.uint8).reshape(5, 6),
            pixel_format=PixelFormat.GRAY8,
        )
        acquired = AcquiredFrame(
            info=self._frame_info(),
            image=crop_image(
                root,
                bounds=Rect(x=1, y=1, width=4, height=3),
            ),
            quality=CaptureQuality(usable=True),
        )
        profile = CaptureBackendProfile(backend_id="desktop.copy")

        class Backend:
            @property
            def profile(self) -> CaptureBackendProfile:
                return profile

            def acquire(self) -> AcquiredFrame:
                return acquired

        result = MaterializingFrameSource(backend=Backend()).capture()

        self.assertIsInstance(result, CapturedFrame)
        assert isinstance(result, CapturedFrame)
        self.assertTrue(result.image.is_materialized)
        self.assertFalse(np.shares_memory(result.pixels, root.pixels))

    def test_frame_source_preserves_unavailable_signal(self) -> None:
        profile = CaptureBackendProfile(
            backend_id="desktop.copy",
            requirements=frozenset(
                {CaptureRequirement.WINDOW_FOREGROUND}
            ),
        )
        unavailable = CaptureUnavailable(
            backend_id="desktop.copy",
            reason=CaptureUnavailableReason.REQUIREMENT_UNMET,
            unmet_requirements=(CaptureRequirement.WINDOW_FOREGROUND,),
        )

        class Backend:
            @property
            def profile(self) -> CaptureBackendProfile:
                return profile

            def acquire(self) -> CaptureUnavailable:
                return unavailable

        result = MaterializingFrameSource(backend=Backend()).capture()

        self.assertIs(result, unavailable)

    def test_frame_source_rejects_undeclared_requirement(self) -> None:
        profile = CaptureBackendProfile(backend_id="desktop.copy")

        class Backend:
            @property
            def profile(self) -> CaptureBackendProfile:
                return profile

            def acquire(self) -> CaptureUnavailable:
                return CaptureUnavailable(
                    backend_id="desktop.copy",
                    reason=CaptureUnavailableReason.REQUIREMENT_UNMET,
                    unmet_requirements=(
                        CaptureRequirement.WINDOW_FOREGROUND,
                    ),
                )

        with self.assertRaisesRegex(
            ValueError,
            "requirements not declared",
        ):
            MaterializingFrameSource(backend=Backend()).capture()

    def test_frame_source_rejects_mismatched_backend_id(self) -> None:
        profile = CaptureBackendProfile(
            backend_id="desktop.copy",
            requirements=frozenset(
                {CaptureRequirement.WINDOW_FOREGROUND}
            ),
        )

        class Backend:
            @property
            def profile(self) -> CaptureBackendProfile:
                return profile

            def acquire(self) -> CaptureUnavailable:
                return CaptureUnavailable(
                    backend_id="other.backend",
                    reason=CaptureUnavailableReason.REQUIREMENT_UNMET,
                    unmet_requirements=(
                        CaptureRequirement.WINDOW_FOREGROUND,
                    ),
                )

        with self.assertRaisesRegex(
            ValueError,
            "backend_id must match backend profile",
        ):
            MaterializingFrameSource(backend=Backend()).capture()


if __name__ == "__main__":
    unittest.main()
