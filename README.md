# Interaction capability framework

This repository provides platform-neutral contracts and adapters for interacting
with an external environment. It is an interaction kernel, not an agent runtime.

The framework owns three capability boundaries:

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
        ▼
Target resolution
bind content-space targets to fresh native window/device coordinates
        │
        ▼
Execution
perform lifecycle, window, pointer, keyboard, text, or navigation operations
        │
        ▼
Execution report
native attempt result returned to the caller
```

## In scope

The repository provides reusable capability contracts and supporting data models
for:

- geometry, immutable rasters, crop, resize, and coordinate transforms;
- visual capture, capture quality, source identity, and pixel provenance;
- clean-content extraction from raw captures;
- target availability and Window, ADB, or future control-channel inspection;
- visual-to-logical target binding and execution-time target resolution;
- lifecycle, window-management, pointer, keyboard, text, and navigation effects;
- optional detector-input and evidence primitives;
- stable public contracts that external extension packages may consume; and
- platform adapters that implement these contracts.

Observation snapshots describe facts acquired at a point in time. They are not
locks. Mutable target identity, readiness, and geometry must be revalidated when
an execution adapter resolves or performs an external effect.

Execution success means that the native backend completed the requested attempt.
It does not claim that an application-level goal or expected state transition was
achieved.

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
    ├── observation
    ├── content and targeting
    ├── execution
    └── optional sensing primitives
                │
                ▼
        platform adapters
```

Core packages must not import external extensions or caller-owned decision, state,
workflow, or semantic models.

See [`docs/architecture/observation_boundaries.md`](docs/architecture/observation_boundaries.md)
for read-only observation families and freshness rules.

See [`docs/architecture/content_boundaries.md`](docs/architecture/content_boundaries.md)
and [`docs/architecture/capture_target_boundaries.md`](docs/architecture/capture_target_boundaries.md)
for content-space, target binding, and execution-time coordinate resolution.

See [`docs/architecture/execution_capabilities.md`](docs/architecture/execution_capabilities.md)
for external-effect capability contracts.
