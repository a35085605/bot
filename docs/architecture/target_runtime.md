# Target Runtime boundary

## Purpose

`observation.target_runtime` models the latest observed operational state of one
logical automation target and its possible control channels.

It is a read-only capability. It answers whether the target is known to exist and
what its configured channels currently report. It does not own shared target or
channel identities, caller policy, channel administration, lifecycle effects, or
input execution.

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

## Shared kernel ownership

Shared nouns are capability-neutral:

```python
from target import TargetId
from control_channel import (
    ControlCapability,
    ControlChannelId,
    ControlChannelKind,
    ControlChannelStatus,
    ReadinessBlocker,
)
```

These packages are depended on by observation, management, execution, platform
verticals, and external extensions. They do not depend on those capability
families.

Target Runtime owns only observation contracts:

- `TargetAvailability`;
- `ControlChannelSnapshot[DetailsT]`;
- `ControlChannelInspector[DetailsT]`;
- `TargetRuntimeSnapshot`; and
- `TargetRuntimeInspector`.

## Target and channel observations

`TargetRuntimeSnapshot.availability` distinguishes `AVAILABLE`, `MISSING`, and
`UNKNOWN`. `UNKNOWN` must not be treated as `MISSING`.

Availability is separate from channel readiness. A target may exist while every
Window, ADB, or future control channel is blocked, unavailable, or unknown. Each
channel has its own identity, status, capabilities, blockers, and detail value.

## Extensible channel contracts

`ControlChannelKind` is a normalized string value rather than a closed enum.
Built-in constants identify Desktop Window and ADB, while an external package may
construct another stable kind such as `ControlChannelKind("webdriver")`.

`ControlChannelSnapshot[DetailsT]` is generic over its platform-owned detail
model. Target Runtime validates observation invariants such as blocker
consistency, unique channel IDs, and the absence of a ready channel for a missing
target. It does not register or discover channel packages.

## Built-in vertical packages

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

The vertical packages own platform detail models and specialized inspector
protocols. They depend on the shared kernel and Target Runtime observation ports;
Target Runtime does not import them.

## Read-only inspection

Target Runtime and platform observation packages do not:

- launch, close, terminate, or restart an application;
- activate, restore, move, or resize a window;
- start, stop, prepare, or recover ADB;
- authorize a device; or
- send pointer, keyboard, text, navigation, or shell input.

Window and ADB administration belongs to `desktop_window.management` and
`adb.management`. Application lifecycle and input operations belong to
`execution` adapters.

## Freshness and execution preflight

A runtime snapshot is timestamped prior evidence, not a lock. Focus, geometry,
process existence, authorization, and transport state can change immediately.
Management results must be followed by fresh observation. Target resolution and
execution adapters must revalidate mutable preconditions immediately before an
external side effect.

The caller owns action selection, retry and fallback policy, and application-level
success criteria.
