from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
import unittest

from control import (
    ControlOperationResult,
    ControlOperationStatus,
    DevicePoint,
    Key,
    KeyChord,
    KeyPress,
    PointerButton,
    PointerClick,
    PointerDrag,
    PointerScroll,
    ScreenPoint,
    ScrollDelta,
    TextEntry,
    WindowActivation,
)


class ControlDomainTest(unittest.TestCase):
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

    def test_scroll_steps_are_backend_neutral_and_non_empty(self) -> None:
        operation = PointerScroll[DevicePoint](
            origin=DevicePoint(100, 200),
            delta=ScrollDelta(vertical_steps=-3),
        )

        self.assertEqual(operation.delta.vertical_steps, -3)
        with self.assertRaises(ValueError):
            ScrollDelta()

    def test_keyboard_models_separate_keys_chords_and_text(self) -> None:
        control = Key(" control ")
        enter = Key("enter")
        chord = KeyChord((control, Key("a")))
        press = KeyPress(
            enter,
            repeat=2,
            interval=timedelta(milliseconds=25),
        )

        self.assertEqual(control.value, "control")
        self.assertEqual(len(chord.keys), 2)
        self.assertEqual(press.repeat, 2)
        self.assertEqual(TextEntry("你好").text, "你好")

        with self.assertRaises(ValueError):
            KeyChord((enter,))
        with self.assertRaises(ValueError):
            KeyChord((enter, enter))
        with self.assertRaises(ValueError):
            TextEntry("")

    def test_window_activation_is_only_a_normalized_request(self) -> None:
        operation = WindowActivation(" hwnd:42 ")
        self.assertEqual(operation.window_id, "hwnd:42")

    def test_operation_result_tracks_only_native_attempt(self) -> None:
        started = datetime(2026, 7, 28, 10, 0, tzinfo=timezone.utc)
        finished = started + timedelta(milliseconds=5)
        result = ControlOperationResult(
            status=ControlOperationStatus.SUCCEEDED,
            backend_id=" win32-send-input ",
            started_at=started,
            finished_at=finished,
        )

        self.assertEqual(result.backend_id, "win32-send-input")
        with self.assertRaises(ValueError):
            ControlOperationResult(
                status=ControlOperationStatus.FAILED,
                backend_id="test",
                started_at=finished,
                finished_at=started,
            )
        with self.assertRaises(ValueError):
            ControlOperationResult(
                status=ControlOperationStatus.FAILED,
                backend_id="test",
                started_at=datetime(2026, 7, 28, 10, 0),
                finished_at=datetime(2026, 7, 28, 10, 0),
            )


if __name__ == "__main__":
    unittest.main()
