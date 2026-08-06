# Target Runtime boundary

## Purpose

The `target_runtime` package models the latest observed operational state of one
logical automation target and its possible control channels.

It is a read-only interaction capability. It answers whether the target is known
to exist and what Window, ADB, or future channels currently report. It does not
own visual interpretation, caller policy, channel preparation, lifecycle effects,
or input execution.

```text
TargetRuntimeInspector
          │
          ▼
TargetRuntimeSnapshot
availability + channel state
          │
          ▼
caller-owned logic
    ┌─────┴─────────────┐
    ▼                   ▼
management          execution preflight
prepare channel     use ready channel
```

The caller may use a runtime snapshot without acquiring pixels, for example to
choose whether to invoke a launch capability for a missing target or a management
capability for a blocked channel.

## Target and channel observations

`TargetRuntimeSnapshot.availability` distinguishes `AVAILABLE`, `MISSING`, and
`UNKNOWN`. `UNKNOWN` must not be treated as `MISSING`.

Availability is separate from channel readiness. A target may exist while every
Window, ADB, or future control channel is blocked, unavailable, or unknown.
Each channel has its own identity, status, capabilities, blockers, and
platform-specific detail.

## Extensible channel contracts

`ControlChannelKind` is a normalized string value rather than a closed enum.
`ControlChannelKind.DESKTOP_WINDOW` and `ControlChannelKind.ADB` remain built-in
constants, while an external package may construct another stable kind such as
`ControlChannelKind("webdriver")` without changing this repository.

`ControlChannelSnapshot[DetailsT]` is generic over its detail model. The core
validates only platform-neutral invariants:

- channel identity and kind types;
- readiness status, capabilities, and blockers;
- blocker consistency with readiness status; and
- the presence of a non-null detail value.

The concrete channel inspector, adapter, or package owns the relationship between
a kind and its detail model. For example, a Window inspector returns
`ControlChannelSnapshot[WindowChannelState]`, while an external WebDriver package
may return its own snapshot specialization.

The core does not register kinds, discover channel packages, or maintain a closed
kind-to-detail mapping. Extension activation remains explicit in the consuming
application's composition root.

## Read-only inspection

The package defines immutable snapshots and inspection ports. Inspection must not
intentionally change the target environment.

Target Runtime does not:

- launch, close, terminate, or restart an application;
- activate, restore, move, or resize a window;
- start, stop, prepare, or recover ADB;
- authorize a device; or
- send pointer, keyboard, text, navigation, or shell input.

Window and ADB preparation operations belong to `management` capability adapters.
Application lifecycle and input operations belong to `execution` adapters.

## Built-in Window and ADB channels

`WindowChannelState` records current operational window facts such as identity,
process, title, client and outer bounds, focus relationship, minimized state,
visibility, and responsiveness.

`AdbChannelState` records server reachability, selected device identity, device
status, authorization, and transport readiness.

These are built-in detail models, not an exhaustive list of supported channel
families. External packages may define additional detail models and inspectors
through the generic channel contracts.

These current runtime facts do not belong in `CapturedFrame`. Capture retains only
the source identity and geometry required to explain one historical raster.

## Per-channel inspection ports

`ControlChannelInspector[ChannelState]` and its Window/ADB specializations allow
platform adapters or test doubles to inspect one channel independently. External
packages may specialize the same generic port with their own channel detail model.
An aggregate `TargetRuntimeInspector` may combine several inspectors into one
snapshot while establishing target-level availability separately.

No channels, or no ready channels, does not prove that the target is missing.

## Freshness and execution preflight

A runtime snapshot is a timestamped prior inspection. Focus, geometry, process
existence, authorization, and transport state can change immediately afterward.

The consuming application may use a snapshot to select a management or execution
operation, but the snapshot is not a lock. Management results must be followed by
fresh observation. Target resolution and execution adapters must revalidate
mutable preconditions immediately before an external side effect.

The framework reports observed state and native operation results. The caller
owns action selection, retry/fallback policy, and application-level success
criteria.

See [Observation boundaries](observation_boundaries.md) for the relationship
between Capture, Target Runtime, Temporal, and caller-owned acquisition logic.

See [Management capabilities](management_capabilities.md) for Window and ADB
preparation contracts.

See [External extensions](extensions.md) for package ownership and explicit
composition rules for additional channel families.
