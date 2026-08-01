from __future__ import annotations

from typing import Protocol, TypeVar

from content import ContentFrame
from execution.domain import (
    ContentPointTarget,
    ExecutionTargetResolution,
)
from observation.target_runtime import ControlChannelId, TargetRuntimeSnapshot


NativePointT = TypeVar("NativePointT", covariant=True)


class ExecutionTargetResolver(Protocol[NativePointT]):
    """Resolve content-space intent into a native execution target.

    Implementations must revalidate the selected runtime channel and current
    geometry immediately before producing the native point. A capture-time
    content-to-screen transform is provenance, not an execution guarantee.
    """

    def resolve_point(
        self,
        *,
        target: ContentPointTarget,
        content: ContentFrame,
        runtime: TargetRuntimeSnapshot,
        channel_id: ControlChannelId,
    ) -> ExecutionTargetResolution[NativePointT]:
        ...
