# Reference Assets

## Purpose

`reference_assets` describes stable visual reference material independently of
any one detector. A reference image may be consumed by template matching, image
hashing, colour analysis, feature matching, or another vision use case.

```text
Persistent storage + structured origin
                  │
                  ▼
       ReferenceAssetResolver
                  │
                  ▼
          ReferenceImage
                  │
        ┌─────────┼─────────┐
        ▼         ▼         ▼
 MatchTemplate  Hash input  Colour input
```

The package separates four concerns:

- storage says where the materialized bytes currently live;
- origin says where the pixels came from;
- `ReferenceImage` owns detector-neutral decoded pixels; and
- each detector adapts the reference image into its own input model.

## Structured origins

A manifest entry uses one of three origin models.

### Content region

`ContentRegionOrigin` identifies a rectangle in one stable authoring-time
`ReferenceContentProfile`. The profile includes the reference content size and
pixel format. It is not a runtime `ContentFrame` from one capture.

### Parent asset region

`AssetRegionOrigin` identifies a rectangle in another reference asset's local
coordinate space. This supports nested definitions such as:

```text
content 1920x1080
└── scene.homepage
    └── control.store_button
```

`ReferenceAssetLineageResolver` composes crop offsets and resize scales through
the parent chain. It returns an asset-local-to-reference-content placement when
the complete chain begins at a content region. It rejects cycles, out-of-bounds
parent regions, and optional parent digest mismatches.

### External resource

`ExternalResourceOrigin` describes pixels derived from a non-capture source,
such as a game asset bundle, archive member, package resource, or authored
image. It may record the source locator, member name, decoder identity, and
source digest.

An external resource has no implied content-space placement. A child of an
external resource also has no content placement unless a separate registration
boundary is introduced later.

## Storage is not origin

`ReferenceAssetStorageDefinition` locates the materialized bytes used at
runtime and can verify their digest. It does not claim that the stored PNG or
raw file is the original source.

For example, an extracted sprite may use:

```text
storage: assets/materialized/store-button.png
origin:  game/ui.bundle, member sprites/store_button
```

This preserves lineage without requiring runtime extraction from the original
game bundle.

## Runtime reference images

`ReferenceImage` contains:

- stable asset key;
- immutable `RasterImage` pixels;
- explicit grayscale, BGR, or BGRA format; and
- an optional detector-neutral coverage mask.

It does not contain template matching thresholds, suppression policy, matching
method, or detector-specific result interpretation.

## Template matching boundary

Template matching owns `MatchTemplate`, which contains only grayscale matching
pixels and an optional mask. It has no asset key, locator, origin, resolution
profile, or provenance.

`ReferenceMatchTemplateFactory` is the application boundary between the two
models:

```text
ReferenceImage(GRAY8)
          │
          ▼
MatchTemplate(gray, mask)
          │
          ▼
TemplateMatchEngine
```

The matching service keeps the reference asset key for result and Evidence
provenance, while the engine receives only detector-local image data.

New code imports asset models, ports, and adapters directly from
`vision.reference_assets`. Template matching imports only `MatchTemplate` and
its detector-specific engine contracts.
