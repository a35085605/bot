# Conditional capture backend requirements

## Purpose

Some capture mechanisms require mutable target conditions before they can
produce reliable pixels. A desktop-copy backend may require the target window to
be visible, restored, foreground, and unobscured, while a window-surface or ADB
backend may have different requirements.

The Capture boundary needs to describe those technical constraints without
hiding target mutations inside an observation operation.

```text
CaptureBackendProfile
    static technical requirements
              │
              ▼
ConditionalFrameCaptureBackend.try_acquire()
              │
      ┌───────┴────────┐
      ▼                ▼
AcquiredFrame    CaptureUnavailable
                      ├── reason
                      ├── unmet requirements
                      └── diagnostic detail
```

This contract does not add orchestration. It only lets an adapter declare what
its capture mechanism needs and return an expected unavailable result when those
conditions are not satisfied.

## Read-only boundary

A conditional capture backend may inspect platform facts required by its own
capture mechanism. It must not intentionally change the target environment.

In particular, `try_acquire()` must not:

- restore or activate a window;
- raise a window or change its topmost state;
- move or resize a window;
- start or reconnect ADB;
- launch or terminate the target; or
- send pointer, keyboard, text, or navigation input.

Those are Execution effects. A future coordinator or orchestration policy may
choose to perform them and retry capture, but that policy is outside this
boundary.

## Backend profile

`CaptureBackendProfile` identifies the backend and declares its static technical
requirements. Current requirement values include:

- `target.available`;
- `window.visible`;
- `window.not_minimized`;
- `window.foreground`;
- `window.unobscured`; and
- `adb.transport_ready`.

Requirements describe the capture mechanism, not the current target state. A
backend that requires foreground capture declares
`CaptureRequirement.WINDOW_FOREGROUND` even when the target is already
foreground.

The profile does not import or embed `TargetRuntimeSnapshot`. Capture remains
independent from the Target Runtime domain, and different platform adapters may
inspect or infer their requirements using different native APIs.

## Typed unavailability

Expected acquisition blockers are returned as `CaptureUnavailable` rather than
being represented by a generic exception. The result distinguishes:

- `REQUIREMENT_UNMET` for one or more declared capture requirements;
- `SOURCE_UNAVAILABLE` when the configured pixel source cannot be acquired;
- `PERMISSION_DENIED` when the platform rejects capture access; and
- `TRANSIENT_FAILURE` for a retryable backend failure.

`REQUIREMENT_UNMET` must name at least one unmet requirement. Other reasons must
not attach unmet requirements.

Example:

```python
CaptureUnavailable(
    backend_id="desktop.copy",
    reason=CaptureUnavailableReason.REQUIREMENT_UNMET,
    unmet_requirements=(CaptureRequirement.WINDOW_FOREGROUND,),
    detail="target window is not foreground",
)
```

The signal is capture-specific. It does not claim that an Execution control
channel is blocked, because capture readiness and input readiness may differ for
the same window or ADB target.

## Materialization boundary

`MaterializingConditionalFrameSource` is the application-facing adapter around a
`ConditionalFrameCaptureBackend`.

- successful `AcquiredFrame` values cross the existing pixel ownership boundary
  and become materialized `CapturedFrame` values;
- `CaptureUnavailable` values are preserved without mutation;
- unavailable backend identity must match the declared profile; and
- unmet requirements must be a subset of the profile requirements.

The existing `FrameCaptureBackend.acquire()` and `MaterializingFrameSource`
contracts remain unchanged for backends whose caller already guarantees that
acquisition is available.

## Future orchestration

A future coordinator may combine:

```text
CaptureBackendProfile
+ TargetRuntimeSnapshot
+ preparation policy
+ Execution capabilities
```

It may then activate or restore a target, inspect Runtime again, and retry
capture. This change deliberately does not define that coordinator, preparation
policy, retry loop, timeout, or state restoration behavior.
