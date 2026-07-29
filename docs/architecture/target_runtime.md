# Target Runtime Boundary

## Purpose

The `target_runtime` package models the latest observed operational state of a
logical automation target. It is separate from visual Capture, Observation
coordination, and the semantic World Model.

```text
Capture / World Model                  Target Runtime
what pixels and semantics exist        whether it can be controlled
              │                                      │
              └──────────────────┬───────────────────┘
                                 ▼
                              Decision
                                 │
                                 ▼
                              Execution
```

The package is read-only. It defines immutable runtime snapshots and a
`TargetRuntimeInspector` port, but it does not activate windows, restore
minimized windows, send mouse or keyboard input, start ADB, reconnect devices,
or execute ADB commands. Those side effects belong to Execution adapters.

## Logical targets and control channels

A logical target may expose more than one control channel. An emulator can, for
example, have both a desktop-window channel and an ADB channel. Each channel has
its own status, capabilities, blockers, and platform-specific observed detail.

Common channel states are:

- `READY`: execution may use the channel and no blocker is present;
- `BLOCKED`: the channel exists but a known precondition is not satisfied;
- `UNAVAILABLE`: the channel cannot currently be used; and
- `UNKNOWN`: readiness has not been established.

Blockers are stable string values such as `window.not_foreground`,
`window.minimized`, `adb.device_missing`, or `adb.unauthorized`. They are data,
not exceptions, because an unavailable target is a normal runtime condition.

## Window state

`WindowChannelState` records current operational window facts:

- target and foreground window identity;
- process ID and title;
- client and outer screen bounds;
- focus relationship; and
- optional minimized, visibility, and responsiveness observations.

These values do not belong to `CapturedFrame`. Capture only retains surface
identity and capture-time geometry required to interpret one pixel frame.
Reading runtime state has no side effect. Setting or restoring focus remains an
Execution responsibility.

## ADB state

`AdbChannelState` records whether the ADB server is reachable, the selected
device serial and state, and whether a transport is ready. It does not start the
server, authorize a device, reconnect a transport, or invoke `adb shell input`.

ADB host and port are adapter configuration or endpoint identity. They should not
be copied into a visual frame merely because a capture adapter used ADB to obtain
pixels.

## Snapshot freshness

A runtime snapshot is only the result of a prior inspection. Focus, geometry,
and transport state can change immediately after inspection, so Execution must
revalidate its preconditions immediately before producing an external side
effect. The runtime snapshot can guide Decision and scheduling, but it is not a
lock or guarantee.

## Adapter boundary

Future adapters may implement `TargetRuntimeInspector` using Win32, X11,
Wayland, macOS accessibility APIs, ADB, emulator APIs, or test doubles. This
module intentionally introduces no concrete adapter or execution controller.

See [Observation boundaries](observation_boundaries.md) for the relationship
between Capture, Target Runtime, Temporal observations, and orchestration.
