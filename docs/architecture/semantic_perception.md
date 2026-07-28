# Evidence to Semantic World Snapshot

## Purpose

The `semantic_perception` package converts detector-independent `EvidenceSet`
values into the semantic observations consumed by `world_model`.

```text
CanonicalViewport + EvidenceSet
              │
              ▼
Declarative evidence requirements
              │
              ├────────► scene hypotheses
              │
              └────────► control observations
                                    │
                                    ▼
                             WorldSnapshot
                                    │
                                    ▼
                           WorldStateTracker
```

The package does not run detectors, interpret detector-specific result objects,
track state across frames, make decisions, or execute input. Rules match stable
Evidence metadata: kind, normalized score, detector identity, and asset keys.

## Scene rules

A `SceneRule` contains one or more `EvidenceRequirement` values. Each
requirement selects its strongest matching evidence item. A complete rule
becomes a `SceneHypothesis`; its confidence is the minimum selected evidence
score so every required signal limits the result.

The highest-scoring hypothesis is resolved only when it reaches the configured
minimum confidence and leads the runner-up by the configured margin. Otherwise,
the snapshot keeps the hypotheses but leaves the scene unresolved.

## Control rules

A `ControlRule` selects the strongest matching localized evidence item and maps
its viewport-root bounds to a `ControlObservation`. Missing or non-localized
evidence produces `Presence.UNKNOWN`; absence of evidence is not treated as
proof that a control is absent. Unusable frames suppress scene resolution and
return configured controls as unknown.

## Context validation

`SemanticSnapshotBuilder` requires the `EvidenceSet` and
`CanonicalViewport` to agree on:

- frame ID
- source ID
- canonical viewport root bounds

The builder stores `CanonicalViewport.frame` in the resulting `WorldSnapshot`.
This derived `FrameInfo` uses viewport-root and a direct viewport-root-to-screen
transform, so the world model never needs the raw capture coordinate space.

The temporary `frame=` compatibility path is valid only when the supplied frame
is already the canonical viewport.

## Example

```python
from evidence import EvidenceKind
from semantic_perception import (
    ControlRule,
    EvidenceRequirement,
    SceneRule,
    SemanticPerceptionConfig,
    SemanticSnapshotBuilder,
)
from world_model import ControlKey, SceneKey

match_kind = EvidenceKind("template.match")
builder = SemanticSnapshotBuilder(
    SemanticPerceptionConfig(
        scene_rules=(
            SceneRule(
                scene=SceneKey("login"),
                requirements=(
                    EvidenceRequirement(
                        kind=match_kind,
                        minimum_score=0.8,
                        asset_key="scene.login",
                    ),
                ),
            ),
        ),
        control_rules=(
            ControlRule(
                control=ControlKey("submit"),
                requirement=EvidenceRequirement(
                    kind=match_kind,
                    minimum_score=0.8,
                    asset_key="ui.submit",
                ),
                enabled=True,
            ),
        ),
    )
)

snapshot = builder.build(
    viewport=perception_viewport.viewport,
    quality=frame.quality,
    evidence_set=evidence_set,
)
```
