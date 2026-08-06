# Management capabilities

## Purpose

The `management` package owns optional side-effect capabilities that prepare or
maintain a control channel before application interaction. It sits between
read-only Target Runtime observation and caller-selected Execution.

```text
TargetRuntimeSnapshot
        │
        ▼
caller-owned policy
        │
        ├── channel already ready ───────────────► execution preflight
        │
        └── preparation required
                    │
                    ▼
               management
                    │
                    ▼
            observe runtime again
```

Management never decides that preparation is required. The caller chooses whether
to invoke a management capability, retry it, select another channel, or stop.

## Window management

`management.window` is the canonical port namespace for:

- activation;
- minimize and restore;
- move and resize; and
- atomic outer-bounds changes when supported.

Window command models remain shared with `execution.window.domain` during the
first migration stage so existing imports and native-coordinate types remain
compatible. `execution.window.ports` is a compatibility facade that re-exports
the management ports and owns no implementation.

An activation request is not a focus guarantee. A move or resize result does not
prove that the requested geometry persisted. Callers observe Target Runtime again
to establish the current window facts.

## ADB management

`management.adb` defines explicit capabilities for:

- starting and stopping the configured ADB server;
- preparing one configured ADB control channel; and
- recovering a previously configured transport.

Transport operations address a stable `ControlChannelId`. An adapter may be
configured with server endpoints, device selection, credentials, or native
transport details outside these core operation values.

Management does not authorize a device automatically, choose a device, or hide
retry and fallback policy inside observation. Expected blockers remain visible
through the next `AdbChannelState`.

## Operation results

The first migration stage reuses `ExecutionOperationResult` as the synchronous
native-attempt report for management ports. Success means that the backend
completed its requested native operation. It does not prove that the server or
transport is now ready, or that a window reached its desired state.

Callers must reacquire Target Runtime state before relying on the changed
condition.

## Dependency direction

```text
observation.target_runtime ───► caller preparation decision
                                         │
                                         ▼
                                 management ports
                                         │
                                         ▼
                                  platform adapters
                                         │
                                         ▼
                              fresh runtime observation

fresh runtime + content ──────► execution preflight and input
```

Management packages must not inspect visual semantics, choose policy, schedule
retries, or claim application-level success.

## Migration status

This is the first boundary-migration stage:

- Window management ports are canonical under `management.window`.
- `execution.window.ports` remains as a compatibility facade.
- Window command models remain under `execution.window.domain`.
- ADB server and transport management contracts are newly explicit.
- Target lifecycle and application input remain under `execution`.

Moving shared native-coordinate and operation-result values to a neutral package,
or removing compatibility imports, is intentionally deferred.
