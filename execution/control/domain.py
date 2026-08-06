"""Compatibility exports for shared native control values.

Native coordinates and operation results are no longer owned by execution. New
code should import them from ``native_coordinates`` and ``native_operation``.
"""

from native_coordinates import DevicePoint, ScreenPoint
from native_operation import NativeOperationResult, NativeOperationStatus

ExecutionOperationResult = NativeOperationResult
ExecutionOperationStatus = NativeOperationStatus

__all__ = [
    "DevicePoint",
    "ExecutionOperationResult",
    "ExecutionOperationStatus",
    "ScreenPoint",
]
