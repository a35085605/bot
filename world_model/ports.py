from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta
from typing import Protocol

from world_model.identities import (
    ControlKey,
    IndicatorKey,
    SceneKey,
    ValueKey,
)
from world_model.models import (
    ControlObservation,
    IndicatorObservation,
    ValueObservation,
    WorldSnapshot,
)


class DecisionWorld(Protocol):
    """Read-only semantic world view consumed by decision policies."""

    @property
    def scene(self) -> SceneKey | None:
        ...

    @property
    def latest_snapshot(self) -> WorldSnapshot:
        ...

    @property
    def controls(
        self,
    ) -> Mapping[ControlKey, ControlObservation]:
        ...

    @property
    def indicators(
        self,
    ) -> Mapping[IndicatorKey, IndicatorObservation]:
        ...

    @property
    def values(
        self,
    ) -> Mapping[ValueKey, ValueObservation]:
        ...

    def control(
        self,
        key: ControlKey,
    ) -> ControlObservation | None:
        ...

    def indicator(
        self,
        key: IndicatorKey,
    ) -> IndicatorObservation | None:
        ...

    def observed_value(
        self,
        key: ValueKey,
    ) -> ValueObservation | None:
        ...

    def is_fresh(
        self,
        now: datetime,
        *,
        max_age: timedelta,
    ) -> bool:
        ...
