# Public namespace facades

## Purpose

Public package roots should expose one coherent concept. They are not registries
for every type implemented below the package.

This keeps imports explicit, prevents unrelated capability families from becoming
coupled through convenience re-exports, and makes ownership visible at each call
site.

## Observation

The `observation` root owns only cross-family grouping values:

```python
from observation import ObservationBundle, ObservationCoherence
```

Individual environment-observation families are imported from the package that
owns them:

```python
from observation.capture import CapturedFrame, FrameId
from observation.target_runtime import TargetRuntimeSnapshot
```

Importing `observation` must not implicitly import or re-export every Capture or
Target Runtime contract.

## Execution

The `execution` root owns execution-time target-resolution contracts:

```python
from execution import ContentPointTarget, ExecutionTargetResolver
```

Input and lifecycle are independent capability families:

```python
from execution.input import PointerClick, PointerClicker
from execution.lifecycle import TargetLaunch, TargetLauncher
```

The root package must not flatten input and lifecycle commands or ports into one
large API.

## Geometry

Geometry is a small shared value package, so its root is the stable facade for
the core primitives:

```python
from geometry import Point, Rect, RelativePoint, Size
```

The underlying modules remain implementation locations. Consumers should prefer
the root facade unless they specifically need an internal module.

## Canonical-import rule

Core packages, tests, documentation, and external extensions should import a
contract from the narrowest public namespace that owns it. Removed broad
re-exports do not retain compatibility aliases; callers migrate to the canonical
owner instead.
