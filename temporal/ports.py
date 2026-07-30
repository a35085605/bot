from __future__ import annotations

from datetime import datetime, timedelta
from typing import Protocol, TypeVar, runtime_checkable

from temporal.models import MisfirePolicy, ScheduleToken


ScheduledEventT = TypeVar("ScheduledEventT", contravariant=True)


class Clock(Protocol):
    """Injectable, read-only source for wall-clock and monotonic time.

    The two readings serve different policies: wall-clock time supports dates and
    schedules, while monotonic time supports elapsed duration and freshness. A
    Clock reports time only; it does not own scheduling, timeout, or retry policy.
    """

    def now(self) -> datetime:
        """Return the current timezone-aware wall-clock time."""
        ...

    def monotonic(self) -> float:
        """Return a non-decreasing process-local time value in seconds."""
        ...


@runtime_checkable
class CalendarSchedule(Protocol):
    """Caller-owned rule for timezone-aware recurring occurrences.

    The scheduler uses this rule to determine its next deadline. The rule describes
    calendar timing only; it does not execute callbacks or domain side effects.
    """

    def next_after(self, instant: datetime) -> datetime | None:
        """Return the next timezone-aware occurrence strictly after ``instant``."""
        ...


@runtime_checkable
class TemporalScheduler(Protocol[ScheduledEventT]):
    """Register data events for non-polling temporal delivery.

    Implementations wait efficiently and deliver the supplied event through their
    configured orchestration or event-queue adapter. They must not invoke domain
    control effects directly. Calendar deadlines use wall-clock time; relative
    delays use monotonic time.
    """

    def schedule_at(
        self,
        deadline: datetime,
        event: ScheduledEventT,
        *,
        misfire_policy: MisfirePolicy = MisfirePolicy.FIRE_ONCE,
    ) -> ScheduleToken:
        """Register a one-shot event for a timezone-aware wall-clock deadline."""
        ...

    def schedule_after(
        self,
        delay: timedelta,
        event: ScheduledEventT,
    ) -> ScheduleToken:
        """Register a one-shot event after a positive monotonic duration."""
        ...

    def schedule_recurring(
        self,
        schedule: CalendarSchedule,
        event: ScheduledEventT,
        *,
        misfire_policy: MisfirePolicy = MisfirePolicy.FIRE_ONCE,
    ) -> ScheduleToken:
        """Register an event for each occurrence produced by ``schedule``."""
        ...

    def cancel(self, token: ScheduleToken) -> bool:
        """Cancel a registration, returning whether it was still active."""
        ...
