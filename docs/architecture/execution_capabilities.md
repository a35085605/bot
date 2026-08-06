# Execution capabilities

## Purpose

The `execution` package owns contracts for caller-selected application
interaction. Target Runtime remains read-only, while channel or host
administration belongs to platform management packages.

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
- `execution.input`: pointer, keyboard, text, and navigation operations; and
- `execution.ports`: execution-time target resolution.

Shared native-coordinate values live under `native_coordinates`, while synchronous
native-attempt reports live under `native_operation`. The `execution.control`
namespace remains as a compatibility facade for their previous names.

Window activation and geometry management are canonical under
`desktop_window.management`. The `management.window` and `execution.window`
namespaces remain temporarily for import compatibility.

No adapter is required to implement every family. A desktop adapter may expose
Window management and screen-input capabilities, while an ADB adapter may expose
transport management, device input, and lifecycle capabilities.

## Shared native operation result

Execution capability ports return `NativeOperationResult`. Success means only that
the backend completed the requested native attempt. It does not prove that:

- a target became available or missing;
- a control channel became ready;
- a Window remained focused or reached the requested geometry;
- the intended semantic control received input; or
- an expected world-state transition occurred.

Those facts must be acquired again through observation and evaluated by
caller-owned effect verification.

`ExecutionOperationResult` and `ExecutionOperationStatus` remain compatibility
aliases to `NativeOperationResult` and `NativeOperationStatus`.

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

Window-management commands and ports are canonical under
`desktop_window.management`. Existing imports from `management.window`,
`execution.window`, and the top-level `execution` package resolve to the same
objects during the staged migration.

New code should use `desktop_window.management`.

See [Management capabilities](management_capabilities.md) for activation,
minimize, restore, move, resize, bounds, and ADB administration contracts.

## Input

Input contracts remain backend-neutral and retain the existing capability split:

- pointer move, click, scroll, and drag;
- physical key state, presses, and chords;
- text entry; and
- Back navigation.

`native_coordinates.ScreenPoint` permits negative virtual-screen coordinates.
`native_coordinates.DevicePoint` rejects negative coordinates. Existing imports
from `execution.control` and `execution` resolve to those same types.

Conversion from content-space intent to either native space remains the
responsibility of `ExecutionTargetResolver` immediately before an input effect.

## Dependency direction

```text
target_runtime ───────────────► execution orchestration and preflight
content ──────────────────────► execution target resolution
native_coordinates ──────────► input operations and target resolution
native_operation ────────────► lifecycle / input / management ports
execution capability ports ──► concrete platform adapters

target_runtime ───────────────► management decision and administration
desktop_window.management ───► concrete desktop adapters
adb.management ──────────────► concrete ADB adapters
```

Execution capability packages must not inspect visual semantics, choose policy,
or claim application-level success. They expose synchronous native operations
that higher-level orchestration can select, sequence, and verify.

## Compatibility

`execution.control` is retained temporarily as a compatibility facade for native
coordinates and operation-result names.

`execution.window` is retained temporarily as a compatibility facade for
`desktop_window.management`.
