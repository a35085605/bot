# Canonical viewport boundary

## Purpose

The automation pipeline needs one clean coordinate space that is shared across
capture integration, perception, the world model, and execution planning.

That coordinate space is the **canonical viewport**:

```text
CapturedFrame (raw capture-root)
        │
        │ viewport extraction / registration
        ▼
CanonicalViewport (viewport-root)
        ├────────► PerceptionViewport pixels
        ├────────► Evidence and WorldSnapshot bounds
        └────────► Execution coordinate mapping
```

`CanonicalViewport` lives in the top-level `viewport` package because it is not
owned by Observation, Perception, or Control:

- Observation supplies the raw capture frame and its capture-root-to-screen
  transform.
- Perception supplies or consumes pixels expressed in viewport-root.
- The World Model stores semantic bounds expressed in viewport-root.
- Execution resolves those semantic bounds through the same viewport mapping
  before invoking a native control channel.

The viewport package contains no pixels, detector types, semantic identities,
or control operations.

## Canonical frame

`CanonicalViewport.frame` is a derived `FrameInfo` whose `root_bounds` describe
viewport-root rather than raw capture-root.

The derived frame preserves observation identity and timing:

- frame ID
- capture stream ID
- capture timestamp
- source ID
- window context
- capture backend

Its `root_to_screen` transform is composed from:

```text
viewport-root
    │ ViewportPlacement
    ▼
capture-root
    │ observation FrameInfo.root_to_screen
    ▼
screen
```

Semantic perception passes this canonical frame into `WorldSnapshot`. The world
model therefore remains based on `FrameInfo`, but the frame is explicitly the
canonical viewport frame rather than the raw capture frame.

## Placement contract

`ViewportPlacement` records:

- `root_bounds`: canonical viewport-root bounds, always beginning at `(0, 0)`
- `source_bounds_capture`: the raw capture-root region represented by the
  canonical viewport

The rectangles may have different sizes. This allows a future extractor or
registration stage to normalize a capture crop to a reference resolution
without changing downstream coordinate contracts.

Rectangle mapping uses floor for leading edges and ceil for trailing edges so
the mapped half-open rectangle contains the complete source area.

## Pixels remain outside the shared domain

`PerceptionViewport` remains in `perception_integration` and combines:

- `CanonicalViewport`
- immutable pixels
- pixel format
- extraction provenance
- extraction confidence

This keeps image payloads and extraction policy out of the shared viewport
domain while allowing all downstream layers to use the same coordinate
contract.

## Compatibility path

`SemanticSnapshotBuilder.build(frame=...)` remains temporarily available for a
capture that is already the canonical viewport. It creates an identity
`CanonicalViewport`.

New orchestration should pass `viewport=...` explicitly. Cropped or normalized
captures must not use the compatibility path because raw capture-root and
viewport-root are different coordinate spaces.

## Non-goals

This boundary does not decide:

- which viewport extractor to use
- how to discover black bars or window chrome
- how to normalize a viewport to a template reference resolution
- which detector or ROI to run
- which control channel to select
- whether an application-level effect succeeded
