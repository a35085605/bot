# Execution capabilities

## Purpose

The `execution` package owns contracts for caller-selected application
interaction. `target_runtime` remains read-only, while optional channel or host
preparation belongs to `management`.

```text
Fresh Target Runtime snapshots
          │
          ▼
Execution orchestration and preflight
    ┌─────┼──────────────┐
    ▼     ▼              ▼
lifecycle input   target resolution
    │     │              │
    └─────┴──────────────┘
                  │
                  ▼
          platform adapters
```

The package is divided into independently implementable capability families:

- `execution.lifecycle`: launch, orderly close, forced termination, and restart;
- `execution.input`: pointer, keyboard, text, and navigation operations;
- `execution.control`: shared native coordinate and operation-result values; and
- `execution.ports`: execution-time target resolution.

Window activation and geometry management are canonical under
`management.window`. The `execution.window` namespace remains temporarily for
import compatibility.

No adapter is required to implement every family. A desktop adapter may expose
window-management and screen-input capabilities, while an ADB adapter may expose
transport-management, device-input, and lifecycle capabilities.

## Shared operation result

Execution capability ports return `ExecutionOperationResult`. The first
management migration stage also reuses this result for synchronous management
attempts. Success means only that the backend completed the requested native
attempt. It does not prove that:

- a target became available or missing;
- a control channel became ready;
- a window remained focused or reached the requested geometry;
- the intended semantic control received input; or
- an expected world-state transition occurred.

Those facts must be acquired again through observation and evaluated by caller
owned effect verification.

## Lifecycle

Lifecycle commands are target-aware and carry `TargetId`:

- `TargetLaunch` / `TargetLauncher`;
- `TargetClose` / `TargetCloser` for an orderly shutdown request;
- `TargetTermination` / `TargetTerminator` for forced termination; and
- `TargetRestart` / `TargetRestarter`.

A restart adapter may use a native supervisor restart operation. Orchestration may
instead compose close or terminate, observe `MISSING`, launch, and observe
`AVAILABLE`. The port does not prescribe retry, timeout, or verification policy.

## Window compatibility

Window commands address one native `window_id` and remain available from
`execution.window` and the top-level `execution` package during the migration.
The canonical management ports now live under `management.window`.

New code should import window-management ports from `management.window`.
`execution.window.ports` re-exports those ports and owns no implementation.

See [Management capabilities](management_capabilities.md) for activation,
minimize, restore, move, resize, bounds, and ADB preparation contracts.

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
execution.control ────────────► lifecycle / input ports
execution capability ports ───► concrete platform adapters

target_runtime ───────────────► management decision and preparation
management ports ─────────────► concrete platform adapters
```

Execution capability packages must not inspect visual semantics, choose policy,
or claim application-level success. They expose synchronous native operations
that higher-level orchestration can select, sequence, and verify.

## Compatibility

The top-level `control` package is retained temporarily as a compatibility facade.
New code should import native values from `execution` or `execution.control`.

The `execution.window` package is also retained during the first management
migration stage. New window-management port imports should use
`management.window`.
