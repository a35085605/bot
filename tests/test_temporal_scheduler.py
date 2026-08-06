from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import unittest

from scheduling import (
    CalendarSchedule,
    MisfirePolicy,
    ScheduleToken,
    TemporalScheduler,
)


@dataclass(frozen=True)
class HourlyAt:
    minute: int = 0

    def next_after(self, instant: datetime) -> datetime:
        next_hour = instant.replace(minute=self.minute, second=0, microsecond=0)
        if next_hour <= instant:
            next_hour += timedelta(hours=1)
        return next_hour


class RecordingScheduler:
    def __init__(self) -> None:
        self.registrations: list[tuple[object, ...]] = []
        self.active: set[ScheduleToken] = set()

    def _record(self, *registration: object) -> ScheduleToken:
        token = ScheduleToken(f"schedule-{len(self.registrations) + 1}")
        self.registrations.append(registration)
        self.active.add(token)
        return token

    def schedule_at(
        self,
        deadline: datetime,
        event: object,
        *,
        misfire_policy: MisfirePolicy = MisfirePolicy.FIRE_ONCE,
    ) -> ScheduleToken:
        return self._record("at", deadline, event, misfire_policy)

    def schedule_after(
        self,
        delay: timedelta,
        event: object,
    ) -> ScheduleToken:
        return self._record("after", delay, event)

    def schedule_recurring(
        self,
        schedule: CalendarSchedule,
        event: object,
        *,
        misfire_policy: MisfirePolicy = MisfirePolicy.FIRE_ONCE,
    ) -> ScheduleToken:
        return self._record("recurring", schedule, event, misfire_policy)

    def cancel(self, token: ScheduleToken) -> bool:
        if token not in self.active:
            return False
        self.active.remove(token)
        return True


class TemporalSchedulerTest(unittest.TestCase):
    def test_schedule_token_is_trimmed_and_non_empty(self) -> None:
        self.assertEqual(ScheduleToken("  hourly-reward  ").value, "hourly-reward")

        with self.assertRaises(ValueError):
            ScheduleToken("   ")
        with self.assertRaises(TypeError):
            ScheduleToken(123)  # type: ignore[arg-type]

    def test_calendar_and_scheduler_ports_support_structural_adapters(self) -> None:
        scheduler = RecordingScheduler()
        schedule = HourlyAt()

        self.assertIsInstance(schedule, CalendarSchedule)
        self.assertIsInstance(scheduler, TemporalScheduler)

    def test_scheduler_registers_data_events_without_callbacks(self) -> None:
        scheduler = RecordingScheduler()
        event = {"kind": "stop_farming", "goal_id": "daily-dungeon"}
        deadline = datetime(2026, 7, 31, 18, 30, tzinfo=timezone.utc)

        token = scheduler.schedule_at(
            deadline,
            event,
            misfire_policy=MisfirePolicy.FIRE_ONCE,
        )

        self.assertEqual(
            scheduler.registrations,
            [("at", deadline, event, MisfirePolicy.FIRE_ONCE)],
        )
        self.assertTrue(scheduler.cancel(token))
        self.assertFalse(scheduler.cancel(token))

    def test_relative_and_recurring_schedules_are_distinct(self) -> None:
        scheduler = RecordingScheduler()
        hourly = HourlyAt()

        scheduler.schedule_after(
            timedelta(seconds=30),
            {"kind": "retry"},
        )
        scheduler.schedule_recurring(
            hourly,
            {"kind": "claim_hourly_reward"},
            misfire_policy=MisfirePolicy.SKIP,
        )

        self.assertEqual(scheduler.registrations[0][0], "after")
        self.assertEqual(scheduler.registrations[1][0], "recurring")
        self.assertEqual(scheduler.registrations[1][3], MisfirePolicy.SKIP)


if __name__ == "__main__":
    unittest.main()
