# Observation boundaries

## Purpose

Observation is an orchestration concept: it coordinates facts acquired from the
external world. It is not synonymous with visual capture.

```text
External world
├── Capture
│   └── pixels, capture geometry, integrity, provenance
├── Target Runtime
│   └── window, ADB, focus, visibility, readiness
└── Temporal
    └── wall-clock date/time and monotonic time

                 ▼
          ObservationBundle
                 ▼
       Perception / Decision / Execution
```

The three boundaries have different adapters, freshness requirements, and
failure semantics. They may be sampled during one orchestration cycle, but they
are not assumed to be atomic.

## Capture

The `capture` package answers:

> What pixels were acquired, how should their coordinates be interpreted, and
> are those pixels usable?

`CapturedFrame` owns immutable pixels, a `FrameInfo` coordinate contract,
pixel format, and `CaptureQuality`.

`FrameInfo.surface` is deliberately limited to capture-time surface identity and
geometry. It does not carry:

- window title or process ID;
- foreground or focus state;
- minimized, visible, or responsive state;
- ADB server address, port, authorization, or transport readiness; or
- execution capability or blockers.

A capture adapter may require a window selector, ADB endpoint, or device serial
to locate its source. Adapter configuration is not automatically capture output.
Only facts required to interpret the returned pixels belong in `CapturedFrame`.

## Capture integrity versus target state

Window occlusion and frame contamination are separate facts.

- Target Runtime may observe that another window covers the target.
- A desktop duplication backend may return those covering pixels.
- A window-surface backend may bypass desktop occlusion entirely.
- A minimized target may produce no frame, a stale frame, a black frame, or a
  valid off-screen frame depending on the backend.

For that reason `CaptureQuality` reports pixel-level results such as `usable`,
`sharpness`, `contaminated`, and diagnostic detail. It does not expose a generic
`occluded` window-state flag.

A backend translates platform-specific preconditions into its capture result.
For example, if a backend cannot capture a background window, it may return a
capture-unavailable result in a future adapter API. Perception should consume the
resulting pixel integrity rather than understand Win32, compositor, or ADB
focus semantics.

## Target Runtime

The `target_runtime` package answers:

> Does the logical automation target exist, and which control channels can be
> used now?

`WindowChannelState` owns current window identity, title, process ID, bounds,
focus, minimized, visibility, and responsiveness observations.
`AdbChannelState` owns current server, device, and transport observations.

These snapshots guide Decision and scheduling, but they are not locks. Execution
must inspect or revalidate mutable preconditions immediately before an external
side effect.

Capture-time geometry and runtime geometry may both exist without being the same
fact:

```text
CapturedFrame.info.surface
= historical geometry needed to interpret one frame

TargetRuntimeSnapshot.window channel
= latest inspected operational geometry and state

Execution preflight
= geometry and readiness revalidated immediately before input
```

## Temporal

The `temporal` package separates two kinds of time:

- timezone-aware wall-clock time for date, schedule, and business rules; and
- monotonic time for elapsed duration, timeout, age, and freshness.

`Clock` is injectable so policies and tests do not depend directly on host time.
`TemporalSnapshot` makes time an explicit observation when current date or time
is part of a decision.

A date displayed inside captured pixels is still visual evidence and must be
interpreted by Vision or Semantic Perception. It is not assumed to equal the host
clock.

## Observation coordination

`ObservationBundle` groups snapshots acquired during one orchestration cycle:

```python
ObservationBundle(
    cycle_id="cycle-42",
    temporal=temporal_snapshot,
    capture=captured_frame,
    runtime=target_runtime_snapshot,
)
```

Each member retains its own timestamp. `ObservationBundle.coherence` exposes the
acquisition skew instead of claiming all members were sampled atomically.
Decision or orchestration policy can reject or refresh a bundle when its skew or
age exceeds a use-case-specific threshold.

A bundle may omit visual capture or runtime state. Clock-only scheduling,
headless API observation, and runtime health checks are valid observation cycles.

## Foreground policy

Being foreground is not inherently a Perception rule.

The system may choose among policies such as:

- continue capture and perception in the background, but block execution;
- reduce observation frequency while the target is unfocused; or
- pause the complete pipeline while the target is unfocused.

Those are orchestration or Decision policies. Perception should stop only when
its actual input is unusable or policy explicitly declines to process it.

## Dependency direction

```text
capture ───────────────► content / perception / world model

target_runtime ────────► decision / execution

temporal ──────────────► orchestration / decision / freshness checks

capture + target_runtime + temporal
                    └──► observation coordination
```

Capture must not import Target Runtime or Execution. Target Runtime must not
mutate the environment. Observation coordination composes snapshots but does not
own platform adapters or side effects.
