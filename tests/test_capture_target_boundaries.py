from __future__ import annotations

from datetime import datetime, timezone
import unittest

from content import ContentFrame, ContentPlacementInCapture
from control_channel import ControlChannelId
from geometry.point import Point
from geometry.rect import Rect
from observation.capture import (
    CaptureCoordinateMapping,
    CaptureStreamId,
    CoordinateSpace,
    CoordinateTransform,
    DeviceDisplaySurface,
    FrameId,
    FrameInfo,
)
from target import TargetId
from visual_target_binding import (
    VisualTargetBinding,
    VisualTargetBindingBasis,
)


class CaptureTargetBoundaryTest(unittest.TestCase):
    def _adb_frame(self) -> FrameInfo:
        return FrameInfo(
            frame_id=FrameId(11),
            stream_id=CaptureStreamId("adb-session"),
            captured_at=datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc),
            root_bounds=Rect(x=0, y=0, width=1080, height=1920),
            source_id="adb:emulator-5554/display:0",
            surface=DeviceDisplaySurface(
                surface_id="emulator-5554/display:0",
                bounds_device=Rect(x=0, y=0, width=1080, height=1920),
                rotation_degrees=0,
            ),
            root_to_screen=None,
            capture_backend_id="adb.screencap",
            additional_mappings=(
                CaptureCoordinateMapping(
                    transform=CoordinateTransform(
                        source=CoordinateSpace.ROOT,
                        target=CoordinateSpace.DEVICE,
                    ),
                    space_id="emulator-5554/display:0",
                ),
            ),
        )

    def test_adb_capture_does_not_claim_host_screen_coordinates(self) -> None:
        frame = self._adb_frame()
        self.assertIsNone(frame.capture_bounds_screen)
        self.assertEqual(
            frame.root_point_to_device(
                Point(x=100, y=200),
                space_id="emulator-5554/display:0",
            ),
            Point(x=100, y=200),
        )
        with self.assertRaisesRegex(ValueError, "mapping is unavailable"):
            frame.root_point_to_screen(Point(x=100, y=200))

    def test_content_composes_crop_into_device_mapping(self) -> None:
        content = ContentFrame(
            capture=self._adb_frame(),
            placement=ContentPlacementInCapture(
                bounds_capture=Rect(x=0, y=80, width=1080, height=1760),
            ),
        )
        self.assertEqual(
            content.frame.root_point_to_device(
                Point(x=100, y=200),
                space_id="emulator-5554/display:0",
            ),
            Point(x=100, y=280),
        )
        self.assertIsNone(content.frame.capture_bounds_screen)

    def test_visual_binding_is_historical_not_runtime_readiness(self) -> None:
        binding = VisualTargetBinding(
            frame_id=FrameId(11),
            source_id="adb:emulator-5554/display:0",
            content_bounds=Rect(x=0, y=0, width=1080, height=1760),
            target_id=TargetId("game"),
            established_at=datetime(2026, 8, 1, 12, 0, 1, tzinfo=timezone.utc),
            basis=VisualTargetBindingBasis.DEVICE_DISPLAY_IDENTITY,
            confidence=1.0,
            channel_id=ControlChannelId("adb"),
            capture_surface_id="emulator-5554/display:0",
        )
        self.assertEqual(binding.target_id, TargetId("game"))
        self.assertEqual(binding.channel_id, ControlChannelId("adb"))
        self.assertFalse(hasattr(binding, "channel_ready"))
        self.assertFalse(hasattr(binding, "current_geometry"))


if __name__ == "__main__":
    unittest.main()
