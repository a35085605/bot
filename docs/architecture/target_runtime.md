# Target Runtime boundary

## Purpose

The `observation.target_runtime` package models the latest observed operational
state of one logical automation target and its possible control channels.

It is a read-only interaction capability. It answers whether the target is known
to exist and what its configured channels currently report. It does not own visual
interpretation, caller policy, channel preparation, lifecycle effects, or input
execution.

```text
TargetRuntimeInspector
          │
          ▼
TargetRuntimeSnapshot
availability + generic channel snapshots
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

## Core ownership

Target Runtime owns only platform-neutral contracts:

- `TargetId`, `ControlChannelId`, and `ReadinessBlocker`;
- `TargetAvailability`, `ControlChannelKind`, `ControlChannelStatus`, and
  `ControlCapability`;
- `ControlChannelSnapshot[DetailsT]`;
- `ControlChannelInspector[DetailsT]`; and
- `TargetRuntimeSnapshot` and `TargetRuntimeInspector`.

The core does not own Window handles, focus state, ADB serials, ADB device state,
or specialized Window/ADB inspector protocols.

## Target and channel observations

`TargetRuntimeSnapshot.availability` distinguishes `AVAILABLE`, `MISSING`, and
`UNKNOWN`. `UNKNOWN` must not be treated as `MISSING`.

Availability is separate from channel readiness. A target may exist while every
Window, ADB, or future control channel is blocked, unavailable, or unknown. Each
channel has its own identity, status, capabilities, blockers, and detail value.

## Extensible channel contracts

`ControlChannelKind` is a normalized string value rather than a closed enum.
`ControlChannelKind.DESKTOP_WINDOW` and `ControlChannelKind.ADB` identify the
built-in channel families, while an external package may construct another stable
kind such as `ControlChannelKind("webdriver")` without changing this repository.

`ControlChannelSnapshot[DetailsT]` is generic over its detail model. The core
validates only platform-neutral invariants:

- channel identity and kind types;
- readiness status, capabilities, and blockers;
- blocker consistency with readiness status; and
- the presence of a non-null detail value.

The concrete channel package owns the relationship between a kind and its detail
model. The core does not register kinds, discover channel packages, or maintain a
closed kind-to-detail mapping.

## Built-in vertical packages

Built-in platform observation contracts are canonical under vertical packages:

```python
from desktop_window.observation import (
    FocusStatus,
    WindowChannelInspector,
    WindowChannelState,
)
from adb.observation import (
    AdbChannelInspector,
    AdbChannelState,
    AdbDeviceStatus,
)
```

`desktop_window.observation` owns desktop-window identity, process, title, client
and outer bounds, focus relationship, minimized state, visibility,
responsiveness, and the specialized read-only inspector protocol.

`adb.observation` owns server reachability, selected device identity, device
status, authorization and transport readiness, plus the specialized read-only
inspector protocol.

These packages depend on the generic Target Runtime contracts. Importing the core
does not import either platform package.

## Read-only inspection

Inspection must not intentionally change the target environment.

Target Runtime and platform observation packages do not:

- launch, close, terminate, or restart an application;
- activate, restore, move, or resize a window;
- start, stop, prepare, or recover ADB;
- authorize a device; or
- send pointer, keyboard, text, navigation, or shell input.

Window and ADB administration operations belong to
`desktop_window.management` and `adb.management`. Application lifecycle and input
operations belong to `execution` adapters.

Current runtime facts do not belong in `CapturedFrame`. Capture retains only the
source identity and geometry required to explain one historical raster.

## Per-channel inspection ports

Platform packages specialize `ControlChannelInspector[DetailsT]` for one channel
family. External packages may do the same with their own detail model. An
aggregate `TargetRuntimeInspector` may combine several inspectors into one
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
administration contracts.

See [External extensions](extensions.md) for package ownership and explicit
composition rules for additional channel families.
