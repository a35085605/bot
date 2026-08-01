# Capture backend requirements

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
FrameCaptureBackend.acquire()
              │
      ┌───────┴────────┐
      ▼                ▼
AcquiredFrame    CaptureUnavailable
                      ├── reason
                      ├── unmet requirements
                      └── diagnostic detail
```

`FrameCaptureBackend` is the single backend contract. Capture availability is
part of its result rather than a separate conditional capability hierarchy.

## Read-only boundary

A capture backend may inspect platform facts required by its own capture
mechanism. It must not intentionally change the target environment.

In particular, `acquire()` must not:

- restore or activate a window;
- raise a window or change its topmost state;
- move or resize a window;
- start or reconnect ADB;
- launch or terminate the target; or
- send pointer, keyboard, text, or navigation input.

Those are Execution effects. A coordinator or orchestration policy may choose to
perform them and retry capture, but that policy is outside this boundary.

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

A backend with no special target preconditions still provides a profile with an
empty requirements set. The profile does not imply that acquisition is
guaranteed: the source may still disappear, permissions may be denied, or a
transient platform failure may occur.

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

`MaterializingFrameSource` is the application-facing adapter around a
`FrameCaptureBackend`.

- successful `AcquiredFrame` values cross the pixel ownership boundary and
  become materialized `CapturedFrame` values;
- `CaptureUnavailable` values are preserved without mutation;
- unavailable backend identity must match the declared profile; and
- unmet requirements must be a subset of the profile requirements.

`CapturedFrameSource.capture()` exposes the same result shape after ownership
normalization: `CapturedFrame | CaptureUnavailable`.

## No guaranteed capture contract

Capture cannot guarantee successful acquisition from inside its own boundary.
Target availability, window state, permissions, and transport readiness are
mutable external facts and may change between any prior inspection and the
actual acquisition attempt.

For that reason there is no separate guaranteed backend or source port. A
coordinator may require a frame for a particular workflow, but that is policy:
it consumes `CaptureUnavailable`, decides whether to prepare the environment,
wait, retry, select another backend, or stop, and then performs another capture
attempt.

```text
CapturedFrameSource.capture()
             │
             ▼
CapturedFrame | CaptureUnavailable
             │
             ▼
Coordinator policy
  use frame / prepare / retry / wait / stop
```

## Coordination

A coordinator may combine:

```text
CaptureBackendProfile
+ TargetRuntimeSnapshot
+ preparation policy
+ Execution capabilities
```

It may then activate or restore a target, inspect Runtime again, and retry
capture. Capture itself does not define that coordinator, preparation policy,
retry loop, timeout, backend fallback, or state restoration behavior.
