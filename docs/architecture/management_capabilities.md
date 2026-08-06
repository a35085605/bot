# Management capabilities

## Purpose

Management owns explicit side-effect capabilities that administer control-channel
and host infrastructure state. This includes preparation and recovery, but also
configuration, suspension, and shutdown operations that may intentionally make a
channel unavailable.

It sits between read-only Target Runtime observation and caller-selected
Execution:

```text
TargetRuntimeSnapshot
        │
        ▼
caller-owned policy
        │
        ├── channel already ready ───────────────► execution preflight
        │
        └── administration required
                    │
                    ▼
               management
                    │
                    ▼
            observe runtime again
```

Management never decides that an operation is required. The caller chooses
whether to invoke a capability, retry it, select another channel, or stop.

## Shared dependencies

Management imports capability-neutral identities directly:

```python
from control_channel import ControlChannelId
```

It must not depend on `observation` merely to obtain target or channel nouns.
Runtime snapshots remain an input to caller policy, not a dependency of management
command models.

## Vertical package ownership

```python
from desktop_window.management import WindowActivator, WindowMove
from adb.management import AdbTransportPreparer, AdbTransportPreparation
```

Window and ADB management contracts are imported directly from their owning
vertical package.

## Window management

`desktop_window.management` owns activation, minimize and restore, move and
resize, and atomic outer-bounds changes when supported. Native-attempt success is
not a focus or geometry guarantee; callers observe Window state again.

Window-management commands use `native_coordinates.ScreenPoint` for virtual-screen
positions.

## ADB management

`adb.management` owns starting and stopping the configured ADB server, preparing
one configured control channel, and recovering a previously configured transport.
Transport operations address a stable `control_channel.ControlChannelId`.

Management does not authorize a device automatically, choose a device, or hide
retry and fallback policy. Expected blockers remain visible through the next ADB
observation.

## Native operation results

Management and Execution ports return `native_operation.NativeOperationResult`.
Success means that the backend completed its requested native attempt. It does not
prove that infrastructure is ready or that an application-level effect occurred.

## Dependency direction

```text
target / control_channel
          │
          ▼
desktop_window.management / adb.management
          │
          ├── native_coordinates
          └── native_operation
                    │
                    ▼
             platform adapters
                    │
                    ▼
          fresh platform observation
```

Management packages must not inspect visual semantics, choose policy, schedule
retries, or claim application-level success.
