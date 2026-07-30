# Execution capabilities

## Purpose

The `execution` package owns contracts that can intentionally change the target
environment. `target_runtime` remains read-only and reports the latest observed
target and channel state.

```text
Target Runtime snapshots
          │
          ▼
Execution orchestration
    ┌─────┼──────────┬─────────┐
    ▼     ▼          ▼         ▼
lifecycle window    input   target resolution
    │     │          │         │
    └─────┴──────────┴─────────┘
                  │
                  ▼
          platform adapters
```

The package is divided into independently implementable capability families:

- `execution.lifecycle`: launch, orderly close, forced termination, and restart;
- `execution.window`: activation, minimize, restore, move, resize, and bounds;
- `execution.input`: pointer, keyboard, text, and navigation operations;
- `execution.control`: shared native coordinate and operation-result values.

No adapter is required to implement every family. A desktop adapter may expose
window and screen-input capabilities, while an ADB adapter may expose device
input and lifecycle capabilities without desktop window management.

## Shared operation result

All capability ports return `ExecutionOperationResult`. Success means only that
the backend completed the requested native attempt. It does not prove that:

- a target became available or missing;
- a window remained focused or reached the requested geometry;
- the intended semantic control received input; or
- an expected world-state transition occurred.

Those facts must be acquired again through observation and evaluated by effect
verification.

## Lifecycle

Lifecycle commands are target-aware and carry `TargetId`:

- `TargetLaunch` / `TargetLauncher`;
- `TargetClose` / `TargetCloser` for an orderly shutdown request;
- `TargetTermination` / `TargetTerminator` for forced termination; and
- `TargetRestart` / `TargetRestarter`.

A restart adapter may use a native supervisor restart operation. Orchestration may
instead compose close or terminate, observe `MISSING`, launch, and observe
`AVAILABLE`. The port does not prescribe retry, timeout, or verification policy.

## Window management

Window commands address one native `window_id` and are split by capability:

- activation requests, which do not guarantee lasting focus;
- minimize and restore;
- move by virtual-screen top-left point;
- resize by positive size; and
- atomic outer-bounds changes when supported.

Window adapters report the native request result. `TargetRuntimeInspector` must
be used afterward to observe focus, minimized state, visibility, responsiveness,
and current geometry.

## Input

Input contracts remain backend-neutral and retain the existing capability split:

- pointer move, click, scroll, and drag;
- physical key state, presses, and chords;
- text entry; and
- Back navigation.

`ScreenPoint` permits negative virtual-screen coordinates. `DevicePoint` rejects
negative coordinates. Conversion from content-space intent to either native
space remains the responsibility of `ExecutionTargetResolver` immediately before
an input effect.

## Dependency direction

```text
target_runtime ───────────────► execution orchestration and preflight
content ──────────────────────► execution target resolution
execution.control ────────────► lifecycle / window / input ports
execution capability ports ───► concrete platform adapters
```

Execution capability packages must not inspect visual semantics, choose policy,
or claim application-level success. They expose synchronous native operations
that higher-level orchestration can select, sequence, and verify.

## Compatibility

The top-level `control` package is retained temporarily as a compatibility facade.
New code should import from `execution`, `execution.input`, `execution.window`, or
`execution.control`. The facade owns no implementation.
