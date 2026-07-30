# Target Runtime boundary

## Purpose

The `target_runtime` package models the latest observed operational state of one
logical automation target and its potential control channels.

It is an observation boundary. It answers whether the target is known to exist
and what Window, ADB, or future control channels currently report. It does not
own visual interpretation, agent policy, application lifecycle effects, or input
execution.

```text
Capture / Semantic World State          Target Runtime
what pixels and UI semantics exist      whether the target exists and how its
                                        control channels are operating
                 │                                      │
                 └──────────────────┬───────────────────┘
                                    ▼
                                 Decision
                                    │
                                    ▼
                                 Execution
```

The visual branch is optional. A runtime snapshot that reports a missing target
can support a launch decision without acquiring a frame.

## Why the name Target Runtime

`Target Runtime` means the target's time-sensitive operating condition. It does
not refer to the Python runtime, an agent execution runtime, or a component that
runs the target.

The boundary contains two levels of observation:

- target-level availability, which distinguishes `AVAILABLE`, `MISSING`, and
  `UNKNOWN`; and
- channel-level state, which describes Window, ADB, or other ways the target
  might be controlled.

This is broader than `WindowState` or `AdbState`, because one logical target may
expose several channels and can be known missing before any channel exists.

## Read-only inspection

The package defines immutable snapshots and the `TargetRuntimeInspector` port.
Inspection must not intentionally change the target environment.

In particular, Target Runtime does not:

- launch or terminate an application;
- activate or restore a window;
- send mouse, keyboard, text, or navigation input;
- start or reconnect ADB;
- authorize a device; or
- execute ADB shell commands.

Those operations are external effects and belong to Execution adapters.

## Target availability

`TargetRuntimeSnapshot.availability` is a target-level fact:

- `AVAILABLE` means the inspector established that the logical target exists;
- `MISSING` means the inspector established that it does not currently exist;
- `UNKNOWN` means existence was not established.

`UNKNOWN` must not be treated as `MISSING`. An inspection failure, insufficient
permissions, ambiguous identity, or unavailable platform API must not cause the
agent to repeatedly relaunch a target that may already be running.

Availability is also separate from channel readiness. A target may be available
while every channel is blocked or unavailable.

## Logical targets and control channels

A logical target may expose more than one control channel. An emulator can, for
example, have both a desktop-window channel and an ADB channel. Each channel has
its own identity, status, capabilities, blockers, and platform-specific observed
detail.

Common channel states are:

- `READY`: Execution may use the channel and no blocker is present;
- `BLOCKED`: the channel exists but a known precondition is not satisfied;
- `UNAVAILABLE`: the channel cannot currently be used; and
- `UNKNOWN`: readiness has not been established.

Blockers are stable string values such as `window.not_foreground`,
`window.minimized`, `adb.device_missing`, or `adb.unauthorized`. They are data,
not exceptions, because blocked and unavailable channels are normal runtime
conditions.

## Window state

`WindowChannelState` records current operational window facts:

- target and foreground window identity;
- process ID and title;
- client and outer screen bounds;
- focus relationship; and
- optional minimized, visibility, and responsiveness observations.

These values do not belong to `CapturedFrame`. Capture retains only surface
identity and capture-time geometry needed to interpret one historical pixel
frame. Reading runtime state has no side effect. Setting or restoring focus
remains an Execution responsibility.

## ADB state

`AdbChannelState` records whether the ADB server is reachable, the selected
device serial and device status, and whether a transport is ready. It does not
start the server, authorize a device, reconnect a transport, or invoke
`adb shell input`.

ADB host and port are adapter configuration or endpoint identity. They should not
be copied into a visual frame merely because a capture adapter used ADB to obtain
pixels.

## Snapshot freshness

A runtime snapshot is a timestamped result of a prior inspection. Focus,
geometry, process existence, and transport state can change immediately after
inspection.

The snapshot can guide Decision and scheduling, but it is not a lock or an
execution guarantee. Execution must revalidate mutable preconditions immediately
before producing an external side effect.

## Adapter boundary

Adapters may implement `TargetRuntimeInspector` using Win32, X11, Wayland,
macOS accessibility APIs, process inspection, ADB, emulator APIs, or test
doubles. An adapter may combine several platform queries to produce one immutable
snapshot, but it must preserve the read-only contract.

See [Observation boundaries](observation_boundaries.md) for the relationship
between Capture, Target Runtime, Temporal observations, coordination, Decision,
and Execution.
