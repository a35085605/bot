# Interaction capability framework

This repository provides platform-neutral contracts and adapters for interacting
with an external environment. It is an interaction kernel, not an agent runtime.

The framework owns four capability boundaries:

```text
External environment
        │
        ▼
Observation
capture pixels, inspect target/runtime state, and read time
        │
        ▼
Caller-owned logic
interpret observations and choose what should happen
        │
        ├──────────────► Management
        │                prepare or recover Window / ADB control channels
        │                         │
        │                         └────────► observe again
        ▼
Target resolution
bind content-space targets to fresh native window/device coordinates
        │
        ▼
Execution
perform lifecycle, pointer, keyboard, text, or navigation operations
        │
        ▼
Native operation report
attempt result returned to the caller
```

## In scope

The repository provides reusable capability contracts and supporting data models
for:

- geometry, immutable rasters, crop, resize, and coordinate transforms;
- visual capture, capture quality, source identity, and pixel provenance;
- clean-content extraction from raw captures;
- generic target availability and control-channel snapshot contracts;
- built-in Window observation under `desktop_window.observation`;
- built-in ADB observation under `adb.observation`;
- Window management and ADB server or transport preparation capabilities;
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

## Platform observation ownership

`observation.target_runtime` owns the platform-neutral target and channel kernel:
identities, kind and readiness values, generic snapshots, generic inspectors, and
aggregate runtime snapshots.

Built-in platform detail models and specialized inspectors live in vertical
packages:

```python
from adb.observation import AdbChannelInspector, AdbChannelState
from desktop_window.observation import (
    WindowChannelInspector,
    WindowChannelState,
)
```

Previous imports from `observation.target_runtime` remain available as lazy
compatibility aliases. New code should use the vertical package that owns the
platform-specific model.

## External extensions

Extension implementations live outside this repository. The core does not contain
an `extensions/` package and does not vendor, auto-discover, register, version, or
release extension implementations.

A consuming application may install extension packages maintained in separate
repositories and compose them explicitly with this framework's public contracts.
External extensions may depend on those public contracts. Core packages and tests
in this repository must not import external extension packages, and
extension-specific code, tests, documentation, and releases belong with the
extension that owns them.

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
    ├── observation.target_runtime (platform-neutral core)
    ├── desktop_window.observation / adb.observation
    ├── management
    ├── content and targeting
    ├── execution
    └── optional sensing primitives
                │
                ▼
        platform adapters
```

Platform-specific packages depend on the generic Target Runtime contracts. The
Target Runtime core does not eagerly import Window, ADB, external extensions, or
caller-owned decision, state, workflow, or semantic models.

See [`docs/architecture/observation_boundaries.md`](docs/architecture/observation_boundaries.md)
for read-only observation families and freshness rules.

See [`docs/architecture/target_runtime.md`](docs/architecture/target_runtime.md)
for generic channel contracts, vertical platform ownership, and compatibility.

See [`docs/architecture/management_capabilities.md`](docs/architecture/management_capabilities.md)
for Window and ADB channel preparation contracts.

See [`docs/architecture/content_boundaries.md`](docs/architecture/content_boundaries.md)
and [`docs/architecture/capture_target_boundaries.md`](docs/architecture/capture_target_boundaries.md)
for content-space, target binding, and execution-time coordinate resolution.

See [`docs/architecture/execution_capabilities.md`](docs/architecture/execution_capabilities.md)
for application-interaction capability contracts.
