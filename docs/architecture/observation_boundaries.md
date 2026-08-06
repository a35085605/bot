# Observation, temporal, and scheduling boundaries

## Purpose

Observation is the read-only side of the interaction framework that acquires
facts from the external environment without intentionally changing it. The
`observation` namespace owns two independent environment-observation families:

```text
External environment
├── Capture
│   └── pixels, capture geometry, integrity, and provenance
└── Target Runtime
    └── target availability, Window / ADB state, and channel readiness
```

Time is also a read-only input, but it comes from the capability-neutral
`temporal` boundary rather than the environment-observation namespace:

```text
Host clocks ──► temporal ──► TemporalSnapshot
```

Scheduling is separate infrastructure under `scheduling`. Registering or
cancelling delivery is a side effect and therefore does not belong to
Observation or `temporal`.

A caller requests whichever observations and temporal inputs it needs. Capture
is not a mandatory entry point: a caller may inspect runtime availability
without acquiring pixels, read time without inspecting a target, or analyze an
offline capture without a controllable runtime.

The framework transports observations and timing inputs. It does not interpret
them, retain an application state model, or choose an action.

## Terminology

An **observation** is a timestamped fact acquired without intentionally changing
the external environment.

A **snapshot** is one immutable result from a particular read-only boundary.

An **acquisition batch** is a caller-owned grouping of snapshots requested for
one operation. Members are acquired independently and are not assumed to be
atomic or mutually consistent.

## Capture

Capture answers:

> What pixels were acquired, how should their coordinates be interpreted, and
> are those pixels usable?

`FrameCaptureBackend.acquire()` returns either `AcquiredFrame` or
`CaptureUnavailable`. `MaterializingFrameSource` crosses the pixel-ownership
boundary by materializing successful frames while preserving unavailable
results.

A `CapturedFrame` owns immutable pixels, `FrameInfo`, pixel format, and
`CaptureQuality`. Capture-time surface identity and native mappings explain one
historical raster. Capture does not own current focus, minimized state, process
state, ADB readiness, execution capability, or application semantics.

A coordinator or consuming application owns any retry, fallback, preparation,
waiting, or failure policy.

## Target Runtime

Target Runtime answers:

> Does the logical target currently exist, and what do its possible control
> channels currently report?

`TargetRuntimeSnapshot` contains target-level availability plus independently
observed Window, ADB, or future control-channel state. It is read-only and does
not launch applications, activate windows, reconnect devices, or send input.

Runtime state is time-sensitive. A snapshot may help a caller select a channel,
but it is not a lock. Execution-time target resolution must revalidate mutable
identity, readiness, and geometry before an external side effect.

## Temporal

`temporal` separates:

- timezone-aware wall-clock time for dates and calendar deadlines; and
- monotonic time for elapsed duration, timeout, and freshness.

`Clock` is injectable so adapters and callers do not need to depend directly on
host time. `observe_time()` returns a `TemporalSnapshot` that can serve as the
timing anchor for an acquisition batch.

Temporal reports time only. It does not register callbacks, deliver events,
choose retry policy, or perform control effects.

## Scheduling

`scheduling` owns caller-facing contracts for registering and cancelling data
events:

- `CalendarSchedule` describes recurring calendar occurrences;
- `TemporalScheduler` registers one-shot, delayed, or recurring delivery;
- `ScheduleToken` identifies a registration; and
- `MisfirePolicy` describes how missed occurrences are handled.

A scheduler may wait efficiently and deliver events through an orchestration or
event-queue adapter. It must not choose domain work or invoke management or
execution effects directly.

## Optional grouping

`ObservationBundle` is a convenience transport for independently acquired
Capture and Target Runtime snapshots plus a required `TemporalSnapshot` timing
anchor. Each member retains its own timestamp. `ObservationCoherence` reports
acquisition skew relative to the temporal snapshot; it does not claim atomicity,
freshness for a particular use case, or safety for execution.

Consumers decide whether a snapshot is fresh enough and whether a member should
be refreshed or omitted.

## Capture truth, runtime truth, and execution truth

```text
Capture truth       at frame acquisition
Runtime truth       at the latest inspection
Execution truth     immediately before a side effect
```

The same category of fact may appear at more than one boundary without being the
same claim. Capture-time geometry explains historical pixels. Runtime geometry
reports a later inspection. Execution revalidates the conditions required for
the selected native operation.

## Dependency direction

```text
observation.capture ─────────► content and optional sensing extensions
observation.target_runtime ──► caller logic and execution preflight
temporal ────────────────────► observation grouping and caller freshness logic
scheduling ──────────────────► caller orchestration / event delivery

capture + target runtime + temporal
                └────────────► optional ObservationBundle
```

Observation packages must not import caller-owned decision models, workflow
engines, semantic models, state trackers, scheduling adapters, or execution
adapters. `temporal` must remain read-only. `scheduling` must not choose or
perform domain work.
