from __future__ import annotations

from typing import Protocol

from content import CapturedContent
from observation.target_runtime import TargetRuntimeSnapshot
from visual_target_binding.domain import VisualTargetBindingResult


class VisualTargetBinder(Protocol):
    """Associate one visual content region with one logical runtime target.

    Implementations may use capture-request provenance, native surface identity,
    device display identity, runtime geometry, or visual recognition. The result
    is a timestamped association, not current channel readiness or an execution
    guarantee.
    """

    def bind(
        self,
        *,
        content: CapturedContent,
        runtime: TargetRuntimeSnapshot,
    ) -> VisualTargetBindingResult:
        ...
