from __future__ import annotations

from typing import Protocol, TypeVar

from content import ContentFrame
from execution.domain import (
    ContentPointTarget,
    ExecutionTargetResolution,
)
from observation.target_runtime import ControlChannelId, TargetRuntimeSnapshot
from visual_target_binding import VisualTargetBinding


NativePointT = TypeVar("NativePointT", covariant=True)


class ExecutionTargetResolver(Protocol[NativePointT]):
    """Resolve content-space intent into a native execution target.

    Implementations must revalidate the selected runtime channel and current
    geometry immediately before producing the native point. Capture-time native
    mappings are historical provenance, not an execution guarantee. When the
    capture source is broader than one logical target, orchestration establishes
    a ``VisualTargetBinding`` and the resolver validates that association against
    the fresh runtime snapshot.
    """

    def resolve_point(
        self,
        *,
        target: ContentPointTarget,
        content: ContentFrame,
        runtime: TargetRuntimeSnapshot,
        channel_id: ControlChannelId,
        binding: VisualTargetBinding | None = None,
    ) -> ExecutionTargetResolution[NativePointT]:
        ...
