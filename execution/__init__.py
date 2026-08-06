"""Execution-time target-resolution contracts.

Input and lifecycle remain independent capability families. Import those
contracts from ``execution.input`` and ``execution.lifecycle`` rather than
through this root package.
"""

from execution.domain import (
    ContentPointTarget,
    ContentRectTarget,
    ExecutionTargetFailureReason,
    ExecutionTargetResolution,
    ExecutionTargetUnavailable,
    ResolvedExecutionTarget,
)
from execution.ports import ExecutionTargetResolver

__all__ = [
    "ContentPointTarget",
    "ContentRectTarget",
    "ExecutionTargetFailureReason",
    "ExecutionTargetResolution",
    "ExecutionTargetResolver",
    "ExecutionTargetUnavailable",
    "ResolvedExecutionTarget",
]
