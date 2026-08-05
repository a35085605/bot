# Optional extensions

## Purpose

`extensions/` contains opt-in capabilities that build on the interaction kernel
without becoming core dependencies. A consuming application enables an extension
by importing it and wiring its ports and adapters in the application's composition
root.

Extensions are not automatically discovered, registered, imported, or activated.
Removing an extension therefore does not change the public contracts owned by the
core framework.

```text
consuming application
        │
        ├── chooses zero or more extensions
        │       ├── extensions.vision
        │       └── extensions.<another_plugin>
        │
        └── composes extension ports with core contracts and adapters
```

## Dependency rule

The dependency direction is one way:

```text
consumer composition
        │
        ▼
optional extensions
        │
        ▼
public interaction contracts
├── observation
├── content and targeting
├── detector_input and evidence
├── execution
└── imaging and geometry
```

Core packages must not import from `extensions`. An extension may depend on public
core contracts, but the core must remain usable when that extension is absent.
Extensions should not depend on one another unless that relationship is explicit
and documented as part of their public contract.

## Bundled vision extension

`extensions.vision` is the bundled vision plug-in. It currently provides:

- `extensions.vision.reference_assets` for stable decoded visual assets and their
  lineage; and
- `extensions.vision.template_matching` for detector-local template matching,
  suppression policies, and an OpenCV engine adapter.

A consumer opts in through explicit imports:

```python
from extensions.vision.reference_assets import ReferenceImage
from extensions.vision.template_matching.adapters.engines import (
    OpenCVTemplateMatchEngine,
)
```

The application may omit this extension, replace its engine or storage adapters,
or introduce another implementation without changing observation, content,
targeting, or execution packages.

## Adding another plug-in

A repository-local extension uses its own namespace:

```text
extensions/
├── vision/
└── <plugin_name>/
    ├── domain/
    ├── ports/
    ├── application/
    └── adapters/
```

The internal layout may vary, but every plug-in should follow these rules:

1. activation is explicit at the consumer composition root;
2. optional third-party dependencies stay behind the plug-in's import path and
   adapters;
3. the plug-in depends only on public core contracts;
4. core packages never import the plug-in;
5. tests import the plug-in explicitly; and
6. removing or replacing the plug-in does not require changes to the core.

## Import migration

The bundled vision implementation now uses the canonical namespace:

```text
vision.*  ->  extensions.vision.*
```

The old `vision.*` namespace is not retained as a compatibility facade. Consumers
must migrate imports so the optional extension boundary remains visible in code.
