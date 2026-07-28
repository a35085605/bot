# Canonical viewport boundary

## Purpose

The automation pipeline needs a clean image region derived from each raw
capture before perception starts. That region is the **canonical viewport**:

```text
CapturedFrame (raw capture-root)
        │
        │ clean-content extraction
        ▼
CanonicalViewport (content-root)
        ├────────► PerceptionViewport pixels
        ├────────► Evidence and WorldSnapshot bounds
        └────────► Execution coordinate mapping
```

The viewport is tied to one observation. It represents a real sub-rectangle of
that raw capture, such as a client area after title bar, window chrome, desktop
content, or letterbox bars have been removed.

`CanonicalViewport` lives in the top-level `viewport` package because it is not
owned by Observation, Perception, or Control:

- Observation supplies the raw capture frame and its capture-root-to-screen
  transform.
- Capture-specific extraction identifies the clean content rectangle.
- Perception consumes pixels expressed in content-root.
- The World Model stores semantic bounds expressed in content-root.
- Execution resolves those semantic bounds through the same content mapping
  before invoking a native control channel.

The viewport package contains no pixels, detector types, semantic identities,
or control operations.

## Content frame

`CanonicalViewport.frame` is a derived `FrameInfo` whose `root_bounds` describe
the extracted content rather than the complete raw capture.

The derived frame preserves observation identity and timing:

- frame ID
- capture stream ID
- capture timestamp
- source ID
- window context
- capture backend

Its `root_to_screen` transform is composed from:

```text
content-root
    │ ContentPlacement (crop translation only)
    ▼
capture-root
    │ observation FrameInfo.root_to_screen
    ▼
screen
```

Semantic perception passes this content frame into `WorldSnapshot`. The world
model remains based on `FrameInfo`, but the frame explicitly describes the
clean content rather than raw capture-root.

## Placement contract

`ContentPlacement` has one field:

```python
ContentPlacement(
    source_bounds_capture: Rect,
)
```

`source_bounds_capture` is the raw capture-root region represented by the clean
content. Content-root is derived automatically:

```text
Rect(
    x=0,
    y=0,
    width=source_bounds_capture.width,
    height=source_bounds_capture.height,
)
```

This boundary preserves the captured pixel dimensions. Mapping between
content-root and capture-root is translation-only; it never resizes or
normalizes the image.

A temporary `ViewportPlacement` alias remains for downstream compatibility, but
it has the same crop-only constructor and no independent `root_bounds`.

## Pixels remain outside the shared domain

`PerceptionViewport` remains in `perception_integration` and combines:

- `CanonicalViewport`
- immutable clean-content pixels
- pixel format
- extraction provenance
- extraction confidence

The pixel dimensions must exactly match the derived content-root bounds. This
keeps image payloads and extraction policy out of the shared viewport domain
while allowing all downstream layers to use the same coordinate contract.

## Detector preparation owns normalization

ROI selection, resize, padding, reference-resolution registration, and other
normalization happen after clean content has been established. Those operations
belong to `detector_input` and `imaging`, where their detector-local placement
and resize provenance can be recorded explicitly.

## Compatibility path

`SemanticSnapshotBuilder.build(frame=...)` remains temporarily available for a
capture that is already clean content. It creates an identity
`CanonicalViewport`.

New orchestration should pass `viewport=...` explicitly. Cropped captures must
not use the compatibility path because raw capture-root and content-root are
different coordinate spaces.

## Non-goals

This boundary does not decide:

- which content extractor to use
- how to discover title bars, black bars, or window chrome
- how to resize or normalize content for a detector
- which detector or ROI to run
- which control channel to select
- whether an application-level effect succeeded
