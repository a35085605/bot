# Perception viewport boundary

## Purpose

Observation records the pixels produced by a capture backend. Those pixels are
not required to be clean application content: a capture may include desktop
content, window chrome, title bars, or letterbox bars.

Perception must not consume `CapturedFrame` directly. Every observation passes
through the clean-content extraction boundary first:

```text
CapturedFrame (raw capture-root)
    |
    | extract_viewport(frame, extractor=...)
    v
PerceptionViewport
    ├── CanonicalViewport (shared content-root contract)
    └── clean content pixels
    |
    v
Perception / Evidence / World Model
```

The clean content is derived from that specific raw capture. Its dimensions may
change when the captured window changes size; extraction implementations must
resolve the appropriate source rectangle from the current frame or current
capture metadata.

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

- `PerceptionViewport` when complete, usable clean content is available; or
- `ViewportUnavailable` when the raw frame must not enter perception.

This makes clean-content extraction mandatory in orchestration while allowing
the implementation to vary by capture source.

## Initial implementations

The first version supports identity and axis-aligned crop extraction:

- `IdentityViewportExtractor`: the raw capture is already clean content.
- `ConfiguredCropViewportExtractor`: a configured capture-root rectangle is
  cropped from the current frame. This covers fixed desktop/window crops and
  removal of known letterbox bars.

A capture implementation with dynamic chrome or client-area geometry should
provide an extractor that computes `source_bounds_capture` for each frame.

Extractors do not resize pixels. Content-root always starts at `(0, 0)` and has
the exact width and height of the selected raw-capture rectangle.

## Coordinate mapping

The complete coordinate chain is:

```text
detector-local
    │ ImagePlacement (may scale during detector preparation)
    ▼
content-root
    │ ContentPlacement (translation only)
    ▼
capture-root
    │ observation FrameInfo.root_to_screen
    ▼
screen
```

`CanonicalViewport.frame` composes the last two transforms and exposes a direct
content-root-to-screen `FrameInfo`. Evidence and World Model bounds remain in
content-root, while execution can resolve them without reading raw pixels.

## Observation relationship

`FrameInfo.window` is optional. A raw capture may represent a desktop, monitor,
or arbitrary capture region and may extend outside a related window. Window
metadata is contextual information, not a containment invariant.

The raw observation `FrameInfo.root_to_screen` remains authoritative for
capture-root. The derived content frame is authoritative for content-root.

## Perception rule

Perception services and detector orchestration should accept
`PerceptionViewport`, not `CapturedFrame`.

Detector preparation may select an ROI, resize it, and map detector-local
coordinates back into content-root through `ImagePlacement`. Semantic
perception receives the associated `CanonicalViewport`, validates Evidence
against its root bounds, and stores the derived content frame in the World
Snapshot.
