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
whether to invoke a management capability, retry it, select another channel, or
stop.

## Vertical package ownership

Built-in management contracts live with the platform that owns them:

```python
from desktop_window.management import WindowActivator, WindowMove
from adb.management import AdbTransportPreparer, AdbTransportPreparation
```

Window and ADB management contracts are not re-exported through a shared
top-level management namespace. Callers import directly from the owning vertical
package.

## Window management

`desktop_window.management` owns:

- activation;
- minimize and restore;
- move and resize; and
- atomic outer-bounds changes when supported.

An activation request is not a focus guarantee. A move or resize result does not
prove that the requested geometry persisted. Callers observe
`desktop_window.observation.WindowChannelState` again to establish current Window
facts.

Window-management commands use `native_coordinates.ScreenPoint` for
virtual-screen positions.

## ADB management

`adb.management` owns explicit capabilities for:

- starting and stopping the configured ADB server;
- preparing one configured ADB control channel; and
- recovering a previously configured transport.

Transport operations address a stable `ControlChannelId`. An adapter may be
configured with server endpoints, device selection, credentials, or native
transport details outside these core operation values.

Management does not authorize a device automatically, choose a device, or hide
retry and fallback policy inside observation. Expected blockers remain visible
through the next `adb.observation.AdbChannelState`.

## Native operation results

Management and Execution ports return `native_operation.NativeOperationResult`.
Success means that the backend completed its requested native attempt. It does not
prove that a server or transport is now ready, that a Window reached its requested
state, or that an application-level effect occurred.

Callers must reacquire the owning platform observation state before relying on a
changed condition.

## Dependency direction

```text
observation.target_runtime identities
                    │
                    ▼
desktop_window.management / adb.management
          │                       │
          ├── native_coordinates  │
          └──────────┬────────────┘
                     ▼
              native_operation
                     │
                     ▼
              platform adapters
                     │
                     ▼
          fresh platform observation

fresh runtime + content ──────► execution preflight and input
```

Management packages must not inspect visual semantics, choose policy, schedule
retries, or claim application-level success.

## Migration status

The verticalization migration is complete:

- generic target and channel contracts live under
  `observation.target_runtime`;
- Window observation lives under `desktop_window.observation`;
- ADB observation lives under `adb.observation`;
- Window management lives under `desktop_window.management`;
- ADB server and transport management live under `adb.management`;
- neutral native coordinates live under `native_coordinates`; and
- neutral native-attempt results live under `native_operation`.

Moving shared target and channel identities out of the observation namespace, or
adding stronger platform-specific identity types, remains intentionally deferred.
