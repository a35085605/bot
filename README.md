# Interaction capability framework

This repository provides platform-neutral contracts and adapters for interacting
with an external environment. It is an interaction kernel, not an agent runtime.

The framework separates interaction and timing boundaries:

```text
External environment ───────► Observation ───────┐
                              capture/runtime     │
                                                 ▼
Host clocks ────────────────► Temporal ───► Caller-owned logic
                              read time       interpret facts
                                              and choose work
                                                    │
                         ┌──────────────────────────┼─────────────────┐
                         ▼                          ▼                 ▼
                    Scheduling                 Management     Target resolution
                    register data events       prepare or     bind content targets
                                               recover        to fresh coordinates
                                                                  │
                                                                  ▼
                                                              Execution
                                                              perform native
                                                              interactions
                                                                  │
                                                                  ▼
                                                        Native operation report
```

## In scope

The repository provides reusable capability contracts and supporting data models
for:

- logical target identity under `target`;
- shared control-channel identity, kind, readiness, blocker, and capability
  values under `control_channel`;
- geometry, immutable rasters, crop, resize, and coordinate transforms;
- visual capture, capture quality, source identity, and pixel provenance;
- clean-content extraction from raw captures;
- target availability and control-channel observation snapshots;
- wall-clock and monotonic observations under `temporal`;
- event-registration contracts under `scheduling`;
- built-in Window observation under `desktop_window.observation`;
- built-in ADB observation under `adb.observation`;
- Window management under `desktop_window.management`;
- ADB server or transport management under `adb.management`;
- visual-to-logical target binding and execution-time target resolution;
- lifecycle, pointer, keyboard, text, and navigation effects;
- optional detector-input and evidence primitives;
- stable public contracts that external extension packages may consume; and
- platform adapters that implement these contracts.

Observation snapshots describe facts acquired at a point in time. They are not
locks. Mutable target identity, readiness, and geometry must be revalidated when
a management or execution adapter performs an external effect.

A successful management or execution result means that the native backend
completed the requested attempt. It does not claim that a channel became ready,
an application-level goal succeeded, or an expected state transition occurred.

## Shared interaction kernel

Shared nouns do not belong to a capability family:

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

`observation.target_runtime` owns only read-only runtime contracts:
`TargetAvailability`, `ControlChannelSnapshot`, `TargetRuntimeSnapshot`, and their
inspector ports. Management and execution therefore depend on the shared kernel,
not on observation merely to obtain identities or channel vocabulary.

## Temporal and scheduling ownership

`temporal` owns read-only wall-clock and monotonic-time contracts. `scheduling`
owns registration and cancellation of data-event delivery. Scheduling is not an
Observation capability because registering or cancelling delivery is an external
side effect.

## Platform observation ownership

Built-in platform detail models and specialized inspectors live in vertical
packages:

```python
from adb.observation import AdbChannelInspector, AdbChannelState
from desktop_window.observation import (
    WindowChannelInspector,
    WindowChannelState,
)
```

Platform-specific contracts are imported from the vertical package that owns the
model. Target Runtime does not import Window or ADB packages.

## External extensions

Extension implementations live outside this repository. The core does not contain
an `extensions/` package and does not vendor, auto-discover, register, version, or
release extension implementations.

A consuming application may install extension packages maintained in separate
repositories and compose them explicitly with this framework's public contracts.
Core packages and tests in this repository must not import external extension
packages.

See [`docs/architecture/extensions.md`](docs/architecture/extensions.md) for the
dependency and composition rules.

## Out of scope

The repository deliberately does not provide or prescribe:

- decision trees, finite-state machines, behavior trees, or planners;
- goals, policies, workflows, retry strategy, or scheduling policy;
- semantic scene/control models or evidence-fusion rules;
- a world model, cross-frame state stabilization, memory, or transition tracking;
- effect-verification semantics; or
- application- or game-specific automation logic.

Those concerns belong to the consuming application. A script, FSM, rule engine,
LLM agent, or custom state model may use the same interaction capabilities
without becoming a dependency of this framework.

## Dependency direction

```text
consumer composition
├── policy / state / semantics
├── external extension packages
└── interaction contracts from this repository
    ├── target / control_channel
    ├── observation.capture / observation.target_runtime
    ├── temporal / scheduling
    ├── desktop_window.observation / adb.observation
    ├── desktop_window.management / adb.management
    ├── content and targeting
    ├── execution
    └── optional sensing primitives
                │
                ▼
        platform adapters
```

Observation, management, execution, platform packages, and extensions may depend
on `target` and `control_channel`. Those shared packages do not depend on any
capability family or platform package.

See [`docs/architecture/public_namespaces.md`](docs/architecture/public_namespaces.md)
for canonical public imports and narrow package-root facades.

See [`docs/architecture/observation_boundaries.md`](docs/architecture/observation_boundaries.md)
for environment observations, temporal input, scheduling, and freshness rules.

See [`docs/architecture/target_runtime.md`](docs/architecture/target_runtime.md)
for shared-kernel ownership, generic channel snapshots, and vertical platform
observation.

See [`docs/architecture/management_capabilities.md`](docs/architecture/management_capabilities.md)
for Window and ADB channel administration contracts.

See [`docs/architecture/capture_backend_requirements.md`](docs/architecture/capture_backend_requirements.md)
for read-only capture requirements and caller-owned preparation flows.

See [`docs/architecture/content_boundaries.md`](docs/architecture/content_boundaries.md)
and [`docs/architecture/capture_target_boundaries.md`](docs/architecture/capture_target_boundaries.md)
for content-space, target binding, and execution-time coordinate resolution.

See [`docs/architecture/detector_input_preparation.md`](docs/architecture/detector_input_preparation.md)
and [`docs/architecture/evidence_bridge.md`](docs/architecture/evidence_bridge.md)
for detector-input preparation and detector-neutral evidence assembly.

See [`docs/architecture/execution_capabilities.md`](docs/architecture/execution_capabilities.md)
for application-interaction capability contracts.
