from __future__ import annotations

from datetime import datetime, timezone
import unittest

from temporal import observe_time


class FakeClock:
    def now(self) -> datetime:
        return datetime(2026, 7, 29, 18, 0, tzinfo=timezone.utc)

    def monotonic(self) -> float:
        return 42.5


class TemporalTest(unittest.TestCase):
    def test_observe_time_keeps_wall_and_monotonic_time_separate(self) -> None:
        snapshot = observe_time(FakeClock(), observer_id="test.clock")

        self.assertEqual(
            snapshot.observed_at,
            datetime(2026, 7, 29, 18, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(snapshot.monotonic_seconds, 42.5)
        self.assertEqual(snapshot.local_date.isoformat(), "2026-07-29")
        self.assertEqual(snapshot.observer_id, "test.clock")

    def test_temporal_observation_requires_aware_wall_time(self) -> None:
        class NaiveClock:
            def now(self) -> datetime:
                return datetime(2026, 7, 29, 18, 0)

            def monotonic(self) -> float:
                return 1.0

        with self.assertRaises(ValueError):
            observe_time(NaiveClock())


if __name__ == "__main__":
    unittest.main()
