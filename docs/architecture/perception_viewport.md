# Perception viewport boundary

## Purpose

Observation records the pixels produced by a capture backend. Those pixels are
not required to be a clean game image: a capture may include desktop content,
window chrome, or letterbox bars.

Perception must not consume `CapturedFrame` directly. Every observation passes
through the viewport extraction boundary first:

```text
CapturedFrame (raw capture-root)
    |
    | extract_viewport(frame, extractor=...)
    v
PerceptionViewport
    ├── CanonicalViewport (shared viewport-root contract)
    └── clean viewport pixels
    |
    v
Perception / Evidence / World Model
```

The shared coordinate contract lives in the top-level `viewport` package.
Extraction implementations and image payloads remain in
`perception_integration`.

See [Canonical viewport boundary](canonical_viewport.md) for ownership and
cross-layer coordinate rules.

## Function contract

```python
result = extract_viewport(frame, extractor=viewport_extractor)
```

A `ViewportExtractor` is callable and returns either:

- `PerceptionViewport` when a complete, usable viewport is available; or
- `ViewportUnavailable` when the raw frame must not enter perception.

This makes viewport extraction mandatory in orchestration while allowing the
implementation to vary by capture source.

## Initial implementations

The first version supports only identity and axis-aligned crop extraction:

- `IdentityViewportExtractor`: the raw capture is already the clean viewport.
- `ConfiguredCropViewportExtractor`: a configured capture-root rectangle is
  cropped into a viewport. This covers known desktop/window crops and removal
  of known letterbox bars.

These extractors deliberately do not resize pixels. Reference-resolution
registration and detector-input resizing remain later perception-preparation
steps.

`ViewportPlacement` nevertheless permits canonical root bounds and capture
source bounds to have different sizes so future normalization can preserve the
same downstream mapping contract.

## Coordinate mapping

The complete coordinate chain is:

```text
detector-local
    │ ImagePlacement
    ▼
viewport-root
    │ ViewportPlacement
    ▼
capture-root
    │ observation FrameInfo.root_to_screen
    ▼
screen
```

`CanonicalViewport.frame` composes the last two transforms and exposes a direct
viewport-root-to-screen `FrameInfo`. Evidence and World Model bounds therefore
remain in viewport-root, while execution can resolve them without reading raw
pixels.

## Observation relationship

`FrameInfo.window` is optional. A raw capture may represent a desktop, monitor,
or arbitrary capture region and may extend outside a related window. Window
metadata is contextual information, not a containment invariant.

The raw observation `FrameInfo.root_to_screen` remains authoritative for
capture-root. The derived canonical frame is authoritative for viewport-root.

## Perception rule

Perception services and detector orchestration should accept
`PerceptionViewport`, not `CapturedFrame`.

Detector-local coordinates are mapped into viewport-root by `ImagePlacement`.
Semantic perception receives the associated `CanonicalViewport`, validates
Evidence against its root bounds, and stores the derived canonical frame in the
World Snapshot.
