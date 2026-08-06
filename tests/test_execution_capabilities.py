from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
import unittest

from desktop_window.management import (
    WindowActivation,
    WindowBoundsChange,
    WindowMinimize,
    WindowMove,
    WindowResize,
    WindowRestore,
)
from execution import (
    Key,
    KeyChord,
    KeyPress,
    PointerButton,
    PointerClick,
    PointerDrag,
    PointerScroll,
    ScrollDelta,
    TargetClose,
    TargetLaunch,
    TargetRestart,
    TargetTermination,
    TextEntry,
)
from geometry.rect import Rect
from geometry.size import Size
from native_coordinates import DevicePoint, ScreenPoint
from native_operation import NativeOperationResult, NativeOperationStatus
from observation.target_runtime import TargetId


class ExecutionCapabilityDomainTest(unittest.TestCase):
    def test_native_coordinate_types_keep_platform_rules_explicit(self) -> None:
        screen = ScreenPoint(-1200, 50)
        device = DevicePoint(1200, 50)

        self.assertEqual((screen.x, screen.y), (-1200, 50))
        self.assertEqual((device.x, device.y), (1200, 50))

        with self.assertRaises(ValueError):
            DevicePoint(-1, 0)
        with self.assertRaises(TypeError):
            ScreenPoint(True, 0)

    def test_pointer_requests_are_immutable_and_validate_parameters(self) -> None:
        click = PointerClick(
            point=ScreenPoint(10, 20),
            button=PointerButton.RIGHT,
            count=2,
            interval=timedelta(milliseconds=50),
        )
        drag = PointerDrag(
            start=DevicePoint(10, 20),
            end=DevicePoint(50, 80),
            duration=timedelta(milliseconds=300),
        )

        self.assertEqual(click.count, 2)
        self.assertEqual(drag.button, PointerButton.LEFT)
        with self.assertRaises(FrozenInstanceError):
            click.count = 3
        with self.assertRaises(ValueError):
            PointerClick(point=ScreenPoint(0, 0), count=0)
        with self.assertRaises(ValueError):
            PointerDrag(
                start=ScreenPoint(0, 0),
                end=ScreenPoint(1, 1),
                duration=timedelta(milliseconds=-1),
            )

    def test_scroll_keyboard_and_text_models_remain_backend_neutral(self) -> None:
        operation = PointerScroll[DevicePoint](
            origin=DevicePoint(100, 200),
            delta=ScrollDelta(vertical_steps=-3),
        )
        control = Key(" control ")
        enter = Key("enter")
        chord = KeyChord((control, Key("a")))
        press = KeyPress(
            enter,
            repeat=2,
            interval=timedelta(milliseconds=25),
        )

        self.assertEqual(operation.delta.vertical_steps, -3)
        self.assertEqual(control.value, "control")
        self.assertEqual(len(chord.keys), 2)
        self.assertEqual(press.repeat, 2)
        self.assertEqual(TextEntry("你好").text, "你好")

        with self.assertRaises(ValueError):
            ScrollDelta()
        with self.assertRaises(ValueError):
            KeyChord((enter,))
        with self.assertRaises(ValueError):
            TextEntry("")

    def test_lifecycle_commands_are_target_aware(self) -> None:
        target_id = TargetId(" game ")

        self.assertEqual(TargetLaunch(target_id).target_id, TargetId("game"))
        self.assertEqual(TargetClose(target_id).target_id, TargetId("game"))
        self.assertEqual(TargetTermination(target_id).target_id, TargetId("game"))
        self.assertEqual(TargetRestart(target_id).target_id, TargetId("game"))

        with self.assertRaises(TypeError):
            TargetLaunch("game")  # type: ignore[arg-type]

    def test_window_commands_split_state_and_geometry_capabilities(self) -> None:
        window_id = " hwnd:42 "

        self.assertEqual(WindowActivation(window_id).window_id, "hwnd:42")
        self.assertEqual(WindowMinimize(window_id).window_id, "hwnd:42")
        self.assertEqual(WindowRestore(window_id).window_id, "hwnd:42")
        self.assertEqual(
            WindowMove(window_id, ScreenPoint(-100, 20)).top_left_screen,
            ScreenPoint(-100, 20),
        )
        self.assertEqual(
            WindowResize(window_id, Size(1280, 720)).size,
            Size(1280, 720),
        )
        self.assertEqual(
            WindowBoundsChange(
                window_id,
                Rect(x=-100, y=20, width=1280, height=720),
            ).bounds_screen,
            Rect(x=-100, y=20, width=1280, height=720),
        )

    def test_operation_result_reports_native_attempt_only(self) -> None:
        started = datetime(2026, 7, 31, 0, 0, tzinfo=timezone.utc)
        finished = started + timedelta(milliseconds=5)
        result = NativeOperationResult(
            status=NativeOperationStatus.SUCCEEDED,
            backend_id=" win32 ",
            started_at=started,
            finished_at=finished,
        )

        self.assertEqual(result.backend_id, "win32")
        with self.assertRaises(ValueError):
            NativeOperationResult(
                status=NativeOperationStatus.FAILED,
                backend_id="test",
                started_at=finished,
                finished_at=started,
            )


if __name__ == "__main__":
    unittest.main()
