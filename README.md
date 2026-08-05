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
- explicitly opt-in extensions, including the bundled vision plug-in; and
- platform adapters that implement these contracts.

Observation snapshots describe facts acquired at a point in time. They are not
locks. Mutable target identity, readiness, and geometry must be revalidated when
an execution adapter resolves or performs an external effect.

Execution success means that the native backend completed the requested attempt.
It does not claim that an application-level goal or expected state transition was
achieved.

## Optional extensions

Capabilities that are useful but not required by the interaction kernel live
under `extensions/`. They are plug-ins composed explicitly by the consuming
application, not dependencies loaded by the core.

The bundled `extensions.vision` plug-in contains reference-asset and template-
matching capabilities. Consumers may import it, omit it, replace its adapters, or
add another plug-in under `extensions/<name>` without changing the core packages.

```python
from extensions.vision.reference_assets import ReferenceImage
from extensions.vision.template_matching.adapters.engines import (
    OpenCVTemplateMatchEngine,
)
```

Extensions may depend on public interaction contracts. Core packages must not
import extensions, and extensions are not auto-discovered or activated
implicitly. See [`docs/architecture/extensions.md`](docs/architecture/extensions.md)
for the plug-in dependency and composition rules.

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
├── optional extensions
│   └── extensions.vision
└── interaction contracts
    ├── observation
    ├── content and targeting
    ├── execution
    └── optional sensing primitives
                │
                ▼
        platform adapters
```

Core packages must not import extensions or caller-owned decision, state,
workflow, or semantic models.

See [`docs/architecture/observation_boundaries.md`](docs/architecture/observation_boundaries.md)
for read-only observation families and freshness rules.

See [`docs/architecture/content_boundaries.md`](docs/architecture/content_boundaries.md)
and [`docs/architecture/capture_target_boundaries.md`](docs/architecture/capture_target_boundaries.md)
for content-space, target binding, and execution-time coordinate resolution.

See [`docs/architecture/execution_capabilities.md`](docs/architecture/execution_capabilities.md)
for external-effect capability contracts.
