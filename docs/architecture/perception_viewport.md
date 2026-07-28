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
PerceptionViewport (clean viewport-root)
    |
    v
Perception / Evidence / World Model
```

`PerceptionViewport.root_bounds` always starts at `(0, 0)`. Root coordinates
produced after this boundary are viewport-root coordinates.

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

This boundary deliberately does not resize pixels. Reference-resolution
registration and detector-input resizing remain later perception-preparation
steps.

## Coordinate mapping

`ViewportPlacement` records the raw capture-root rectangle represented by the
complete viewport image:

```text
viewport-root --translation--> capture-root --FrameInfo.root_to_screen--> screen
```

A viewport can therefore map points and rectangles back to the raw capture and
to screen coordinates without exposing raw pixels to perception.

For the crop implementation:

```text
capture_x = viewport_x + source_bounds_capture.left
capture_y = viewport_y + source_bounds_capture.top
```

Because v1 extraction does not resize, the viewport dimensions equal the
source crop dimensions.

## Observation relationship

`FrameInfo.window` is optional. A raw capture may represent a desktop, monitor,
or arbitrary capture region and may extend outside a related window. Window
metadata is contextual information, not a containment invariant.

`FrameInfo.root_to_screen` remains the authoritative raw capture-root to screen
mapping.

## Perception rule

Perception services and detector orchestration should accept
`PerceptionViewport`, not `CapturedFrame`.

Detector-local coordinates are mapped into viewport-root by `ImagePlacement`.
Execution later maps viewport-root through capture-root into the native screen
or device coordinate space.
