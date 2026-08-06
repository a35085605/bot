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

Shared identities are imported from `target` and `control_channel`. Shared native
coordinates live under `native_coordinates`, while synchronous native-attempt
reports live under `native_operation`.

Execution must not depend on observation merely to obtain `TargetId` or
`ControlChannelId`. It depends on Target Runtime only when a fresh snapshot is
part of execution preflight.

## Shared native operation result

Execution capability ports return `NativeOperationResult`. Success means only that
the backend completed the requested native attempt. It does not prove that a
target or channel changed state, that the intended semantic control received
input, or that an expected world-state transition occurred.

Those facts must be acquired again through observation and evaluated by
caller-owned effect verification.

## Lifecycle

Lifecycle commands carry `target.TargetId`:

- `TargetLaunch` / `TargetLauncher`;
- `TargetClose` / `TargetCloser`;
- `TargetTermination` / `TargetTerminator`; and
- `TargetRestart` / `TargetRestarter`.

The port does not prescribe retry, timeout, or verification policy.

## Input and target resolution

Input contracts remain backend-neutral: pointer, keyboard, text, and Back
navigation. Conversion from content-space intent to a native coordinate remains
the responsibility of `ExecutionTargetResolver` immediately before an input
effect.

`ExecutionTargetResolver` uses `control_channel.ControlChannelId` together with a
fresh `observation.target_runtime.TargetRuntimeSnapshot`.

## Dependency direction

```text
target / control_channel ─────► lifecycle and target-resolution contracts
observation.target_runtime ───► execution preflight
content ──────────────────────► execution target resolution
native_coordinates ───────────► input operations and target resolution
native_operation ─────────────► lifecycle / input / management ports
execution capability ports ───► concrete platform adapters
```

Execution capability packages must not inspect visual semantics, choose policy,
or claim application-level success.
