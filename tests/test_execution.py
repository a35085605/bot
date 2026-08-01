from __future__ import annotations

from datetime import datetime, timezone
import unittest

from content import ContentFrame, ContentPlacementInCapture
from execution import (
    ContentPointTarget,
    ExecutionTargetFailureReason,
    ExecutionTargetUnavailable,
    ResolvedExecutionTarget,
    ScreenPoint,
)
from geometry.point import Point
from geometry.rect import Rect
from observation.capture import (
    CaptureStreamId,
    CoordinateSpace,
    CoordinateTransform,
    FrameId,
    FrameInfo,
)
from observation.target_runtime import (
    ControlCapability,
    ControlChannelId,
    ControlChannelKind,
    ControlChannelSnapshot,
    ControlChannelStatus,
    FocusStatus,
    TargetAvailability,
    TargetId,
    TargetRuntimeSnapshot,
    WindowChannelState,
)


class FakeDesktopResolver:
    def resolve_point(
        self,
        *,
        target: ContentPointTarget,
        content: ContentFrame,
        runtime: TargetRuntimeSnapshot,
        channel_id: ControlChannelId,
    ) -> ResolvedExecutionTarget[ScreenPoint] | ExecutionTargetUnavailable:
        if target.frame_id != content.capture.frame_id:
            return ExecutionTargetUnavailable(
                ExecutionTargetFailureReason.FRAME_MISMATCH
            )
        if target.source_id != content.capture.source_id:
            return ExecutionTargetUnavailable(
                ExecutionTargetFailureReason.SOURCE_MISMATCH
            )
        if not content.bounds_content.contains_point(
            target.point_content.x,
            target.point_content.y,
        ):
            return ExecutionTargetUnavailable(
                ExecutionTargetFailureReason.TARGET_OUTSIDE_CONTENT
            )

        channel = runtime.channel(channel_id)
        if channel is None or channel.status is not ControlChannelStatus.READY:
            return ExecutionTargetUnavailable(
                ExecutionTargetFailureReason.CHANNEL_NOT_READY
            )

        capture_point = content.content_point_to_capture(target.point_content)
        screen_point = content.capture.root_point_to_screen(capture_point)
        return ResolvedExecutionTarget(
            source_frame_id=target.frame_id,
            source_id=target.source_id,
            target_id=runtime.target_id,
            channel_id=channel_id,
            point_native=ScreenPoint(
                x=screen_point.x,
                y=screen_point.y,
            ),
            resolved_at=runtime.observed_at,
        )


class ExecutionBoundaryTest(unittest.TestCase):
    def _content(self) -> ContentFrame:
        capture = FrameInfo(
            frame_id=FrameId(9),
            stream_id=CaptureStreamId("session-1"),
            captured_at=datetime(
                2026,
                7,
                29,
                12,
                0,
                tzinfo=timezone.utc,
            ),
            root_bounds=Rect(x=0, y=0, width=1920, height=1200),
            source_id="game-window",
            surface=None,
            root_to_screen=CoordinateTransform(
                source=CoordinateSpace.ROOT,
                target=CoordinateSpace.SCREEN,
                offset_x=100,
                offset_y=200,
            ),
            capture_backend_id="test.capture",
        )
        return ContentFrame(
            capture=capture,
            placement=ContentPlacementInCapture(
                bounds_capture=Rect(
                    x=160,
                    y=120,
                    width=1600,
                    height=900,
                )
            ),
        )

    def _runtime(
        self,
        *,
        status: ControlChannelStatus = ControlChannelStatus.READY,
    ) -> TargetRuntimeSnapshot:
        blockers = () if status is ControlChannelStatus.READY else ()
        return TargetRuntimeSnapshot(
            target_id=TargetId("game"),
            observed_at=datetime(
                2026,
                7,
                29,
                12,
                0,
                1,
                tzinfo=timezone.utc,
            ),
            availability=TargetAvailability.AVAILABLE,
            inspector_id="test.runtime",
            channels=(
                ControlChannelSnapshot(
                    channel_id=ControlChannelId("window"),
                    kind=ControlChannelKind.DESKTOP_WINDOW,
                    status=status,
                    details=WindowChannelState(
                        window_id="hwnd:42",
                        foreground_window_id="hwnd:42",
                        process_id=1234,
                        title="Example Game",
                        client_bounds_screen=Rect(
                            x=100,
                            y=200,
                            width=1920,
                            height=1200,
                        ),
                        window_bounds_screen=Rect(
                            x=90,
                            y=170,
                            width=1940,
                            height=1240,
                        ),
                        focus=FocusStatus.TARGET,
                        minimized=False,
                        visible=True,
                        responsive=True,
                    ),
                    capabilities=frozenset({ControlCapability.POINTER}),
                    blockers=blockers,
                ),
            ),
        )

    def test_resolver_produces_native_target_at_execution_boundary(self) -> None:
        content = self._content()
        target = ContentPointTarget(
            frame_id=content.capture.frame_id,
            source_id=content.capture.source_id,
            point_content=Point(x=10, y=20),
        )

        result = FakeDesktopResolver().resolve_point(
            target=target,
            content=content,
            runtime=self._runtime(),
            channel_id=ControlChannelId("window"),
        )

        self.assertIsInstance(result, ResolvedExecutionTarget)
        assert isinstance(result, ResolvedExecutionTarget)
        self.assertEqual(result.point_native, ScreenPoint(x=270, y=340))

    def test_runtime_owns_operational_window_metadata(self) -> None:
        runtime = self._runtime()
        channel = runtime.channel(ControlChannelId("window"))

        self.assertIsNotNone(channel)
        assert channel is not None
        details = channel.details
        assert isinstance(details, WindowChannelState)
        self.assertEqual(details.title, "Example Game")
        self.assertEqual(details.process_id, 1234)
        self.assertEqual(details.focus, FocusStatus.TARGET)

    def test_resolver_rejects_stale_frame_identity(self) -> None:
        content = self._content()
        result = FakeDesktopResolver().resolve_point(
            target=ContentPointTarget(
                frame_id=FrameId(8),
                source_id=content.capture.source_id,
                point_content=Point(x=10, y=20),
            ),
            content=content,
            runtime=self._runtime(),
            channel_id=ControlChannelId("window"),
        )

        self.assertEqual(
            result,
            ExecutionTargetUnavailable(
                ExecutionTargetFailureReason.FRAME_MISMATCH
            ),
        )

    def test_resolver_rejects_target_outside_content(self) -> None:
        content = self._content()
        result = FakeDesktopResolver().resolve_point(
            target=ContentPointTarget(
                frame_id=content.capture.frame_id,
                source_id=content.capture.source_id,
                point_content=Point(x=1600, y=20),
            ),
            content=content,
            runtime=self._runtime(),
            channel_id=ControlChannelId("window"),
        )

        self.assertEqual(
            result,
            ExecutionTargetUnavailable(
                ExecutionTargetFailureReason.TARGET_OUTSIDE_CONTENT
            ),
        )


if __name__ == "__main__":
    unittest.main()
