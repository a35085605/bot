# Target Runtime boundary

## Purpose

The `target_runtime` package models the latest observed operational state of one
logical automation target and its possible control channels.

It is a read-only interaction capability. It answers whether the target is known
to exist and what Window, ADB, or future channels currently report. It does not
own visual interpretation, caller policy, lifecycle effects, or input execution.

```text
TargetRuntimeInspector
          │
          ▼
TargetRuntimeSnapshot
availability + channel state
          │
          ▼
caller-owned logic
          │
          ▼
execution preflight and capability adapter
```

The caller may use a runtime snapshot without acquiring pixels, for example to
choose whether to invoke a launch capability for a missing target.

## Target and channel observations

`TargetRuntimeSnapshot.availability` distinguishes `AVAILABLE`, `MISSING`, and
`UNKNOWN`. `UNKNOWN` must not be treated as `MISSING`.

Availability is separate from channel readiness. A target may exist while every
Window, ADB, or future control channel is blocked, unavailable, or unknown.
Each channel has its own identity, status, capabilities, blockers, and
platform-specific detail.

## Read-only inspection

The package defines immutable snapshots and inspection ports. Inspection must not
intentionally change the target environment.

Target Runtime does not:

- launch, close, terminate, or restart an application;
- activate, restore, move, or resize a window;
- start or reconnect ADB;
- authorize a device; or
- send pointer, keyboard, text, navigation, or shell input.

Those operations belong to `execution` capability adapters.

## Window and ADB channels

`WindowChannelState` records current operational window facts such as identity,
process, title, client and outer bounds, focus relationship, minimized state,
visibility, and responsiveness.

`AdbChannelState` records server reachability, selected device identity, device
status, authorization, and transport readiness.

These current runtime facts do not belong in `CapturedFrame`. Capture retains
only the source identity and geometry required to explain one historical raster.

## Per-channel inspection ports

`ControlChannelInspector[ChannelState]` and its Window/ADB specializations allow
platform adapters or test doubles to inspect one channel independently. An
aggregate `TargetRuntimeInspector` may combine several inspectors into one
snapshot while establishing target-level availability separately.

No channels, or no ready channels, does not prove that the target is missing.

## Freshness and execution preflight

A runtime snapshot is a timestamped prior inspection. Focus, geometry, process
existence, authorization, and transport state can change immediately afterward.

The consuming application may use a snapshot to select an operation or channel,
but the snapshot is not a lock. Target resolution and execution adapters must
revalidate mutable preconditions immediately before an external side effect.

The framework reports observed state and native operation results. The caller
owns action selection, retry/fallback policy, and application-level success
criteria.

See [Observation boundaries](observation_boundaries.md) for the relationship
between Capture, Target Runtime, Temporal, and caller-owned acquisition logic.
