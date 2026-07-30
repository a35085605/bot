# Observation boundaries

## Purpose

Observation is the read-only acquisition side of an agent cycle. It groups facts
obtained from the external world without assuming that every decision begins with
a visual frame.

`Capture`, `Target Runtime`, and `Temporal` are separate observation families:

```text
External world
├── Capture
│   └── pixels, capture geometry, integrity, provenance
├── Target Runtime
│   └── target availability, window / ADB state, channel readiness
└── Temporal
    └── wall-clock date/time and monotonic time

                 independently acquired
                           │
                           ▼
                  ObservationBundle
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
      Perception        Decision       Freshness / scheduling
```

The families have different adapters, freshness requirements, and failure
semantics. They may be sampled during one orchestration cycle, but they are not
assumed to be atomic or mutually required.

## Terminology

An **observation** is a timestamped fact acquired without intentionally changing
the external environment.

A **snapshot** is one immutable result from a particular observation family.

An **observation cycle** is an orchestration attempt to acquire the snapshots
needed for one policy evaluation. The requested set depends on the use case.

An **agent state** or tracked state is a durable interpretation accumulated over
multiple cycles. `ObservationBundle` is not that state: it only transports the
facts acquired for one cycle.

Perception, Decision, and Execution remain separate concerns:

- Perception interprets low-level observations such as pixels.
- Decision combines goals, tracked state, and current observations into intent.
- Execution performs external side effects after revalidating mutable facts.

## Observation families

| Family | Primary question | Typical consumers |
| --- | --- | --- |
| Capture | What pixels were acquired, how are they positioned, and are they usable? | Content, Vision, Semantic Perception |
| Target Runtime | Does the logical target currently exist, and what control channels are operational? | Decision, scheduling, Execution preflight |
| Temporal | What are the current wall-clock and monotonic times? | Scheduling, timeout, freshness, Decision |

A family may be absent from a cycle when it is not relevant. For example:

- launching a missing application can be decided from Target Runtime alone;
- a scheduled wake-up may need only Temporal;
- offline image analysis may need Capture without a controllable target; and
- a visual interaction cycle may use all three families.

## Non-visual decision example

Capture is not the entry point of the agent state machine:

```text
TargetRuntimeInspector
          │
          ▼
TargetRuntimeSnapshot
  availability = MISSING
          │
          ▼
Decision
  goal requires target to be available
          │
          ▼
LaunchTarget intent
          │
          ▼
Execution
  launch process or package
          │
          ▼
TargetRuntimeInspector
  availability = AVAILABLE
```

No frame is required until a later decision needs visual semantics. Failure to
capture a frame must not be used as proof that the target application is missing;
that fact belongs to Target Runtime.

## Capture

The `capture` package answers:

> What pixels were acquired, how should their coordinates be interpreted, and
> are those pixels usable?

`FrameCaptureBackend` is the platform-facing acquisition port. Its `acquire()`
operation returns `AcquiredFrame`, which may still reference a logical read-only
raster slice. `CapturedFrameSource` is the application-facing port that promises
an owned `CapturedFrame`. `MaterializingFrameSource` adapts the former to the
latter by calling `materialize_image()` and constructing `CapturedFrame`.

```text
FrameCaptureBackend.acquire()
             │
             ▼
       AcquiredFrame
             │
             │ materialize_image()
             ▼
 MaterializingFrameSource
             │ implements
             ▼
CapturedFrameSource.capture()
             │
             ▼
       CapturedFrame
```

`CapturedFrame` exposes immutable pixels, `FrameInfo`, pixel format, and
`CaptureQuality`. `FrameInfo.surface` is deliberately limited to capture-time
surface identity and geometry required to interpret that frame. It does not
carry:

- current window title or process state;
- foreground, focus, minimized, visibility, or responsiveness state;
- current ADB authorization or transport readiness; or
- execution capability or blockers.

A capture adapter may use a window selector, ADB endpoint, or device serial to
locate its pixel source. Adapter configuration is not automatically observation
output. Only facts needed to interpret the returned pixels belong in
`CapturedFrame`.

## Capture integrity versus target state

Window state and pixel integrity are separate facts:

- Target Runtime may observe that another window is foreground.
- A desktop-duplication backend may capture covering pixels.
- A window-surface backend may bypass desktop occlusion.
- A minimized target may produce no frame, a stale frame, a black frame, or a
  valid off-screen frame depending on the backend.

For that reason `CaptureQuality` reports pixel-level results such as `usable`,
`sharpness`, `contaminated`, and diagnostic detail. It does not expose a generic
window-state flag.

Perception consumes the resulting pixel integrity. It should not need to
understand Win32, compositor, emulator, or ADB readiness semantics.

## Target Runtime

The `target_runtime` package answers:

> What is the latest observed operational state of this logical automation
> target, and which control channels could Execution use now?

The name refers to the target's time-sensitive operating condition, not a Python
runtime or an execution engine. It includes target-level availability plus
channel-level facts.

`TargetRuntimeSnapshot.availability` distinguishes an available target, a known
missing target, and an unknown result. A missing target is therefore different
from an available target whose channels are blocked or unavailable.

`WindowChannelState` owns current window identity, title, process ID, bounds,
focus, minimized, visibility, and responsiveness observations.
`AdbChannelState` owns current server, device, authorization, and transport
observations.

Target Runtime is read-only. It does not launch or terminate applications,
activate or restore windows, start ADB, reconnect devices, or send input. Those
operations are Execution effects.

Runtime snapshots guide Decision and scheduling, but they are not locks.
Execution must inspect or revalidate mutable preconditions immediately before an
external side effect.

Capture-time geometry and runtime geometry may both exist without representing
the same fact:

```text
CapturedFrame.info.surface
= historical geometry needed to interpret one frame

TargetRuntimeSnapshot window channel
= latest inspected operational geometry and state

Execution preflight
= geometry and readiness revalidated immediately before input
```

## Temporal

The `temporal` package separates two kinds of time:

- timezone-aware wall-clock time for dates, schedules, and business rules; and
- monotonic time for elapsed duration, timeout, age, and freshness.

`Clock` is injectable so policy and tests do not depend directly on host time.
`TemporalSnapshot` makes time an explicit observation when the current date or
time participates in a decision. It also acts as the coherence reference for the
current `ObservationBundle` model.

A timestamp attached to another snapshot describes when that snapshot was
acquired. A `TemporalSnapshot` instead represents time itself as an input to the
cycle.

A date displayed inside captured pixels remains visual evidence and must be
interpreted by Vision or Semantic Perception. It is not assumed to equal the host
clock.

## Observation coordination

`ObservationBundle` groups snapshots requested during one orchestration cycle:

```python
ObservationBundle(
    cycle_id="cycle-42",
    temporal=temporal_snapshot,
    capture=captured_frame,            # optional
    runtime=target_runtime_snapshot,   # optional
)
```

The current model requires `temporal` as the cycle's timing reference. Visual
capture and runtime inspection are optional.

Each member retains its own timestamp. `ObservationBundle.coherence` exposes the
acquisition skew relative to the temporal observation instead of claiming that
all members were sampled atomically. Orchestration or Decision policy can reject
or refresh a bundle when its skew or age exceeds a use-case-specific threshold.

Coordination owns neither the family-specific adapters nor any side effects. It
chooses which observations to request, groups their results, and passes them to
the appropriate consumers.

## Freshness and revalidation

Freshness is use-case specific:

- pixels may remain useful for semantic recognition after a short delay;
- focus and window geometry may become stale immediately;
- ADB transport readiness may change between inspection and input; and
- schedule decisions may require an explicit wall-clock boundary.

Decision may use snapshots to select an intent. Execution still revalidates
mutable safety and targeting preconditions immediately before performing the
intent.

## Foreground policy

Being foreground is not inherently a Perception rule. The system may choose to:

- continue capture and perception in the background but block execution;
- reduce observation frequency while the target is unfocused; or
- pause the complete pipeline while the target is unfocused.

Those are orchestration or Decision policies. Perception should stop only when
its actual input is unusable or policy explicitly declines to process it.

## Dependency direction

```text
capture ───────────────► content / detector input / perception / world model

target_runtime ────────► decision / scheduling / execution preflight

temporal ──────────────► orchestration / decision / freshness checks

capture + target_runtime + temporal
                    └──► observation coordination
```

Capture must not import Target Runtime or Execution. Target Runtime must not
mutate the environment. Temporal must not encode scheduling policy. Observation
coordination composes snapshots but does not own platform adapters, semantic
interpretation, tracked agent state, or side effects.
