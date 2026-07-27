# Detector Result to Evidence Bridge

## Purpose

The bridge contextualizes detector-local output as frame-root `Evidence` while
keeping Observation, Vision primitives, and Evidence independently usable.

```text
prepared detector image + DetectorInputContext
                    │
                    ▼
          detector-local result
                    │
                    ▼
             EvidenceAssembler
                    │
                    ▼
        Evidence in frame root space
```

The bridge is a pure conversion boundary. It does not capture frames, run a
detector, select a detector, assign semantic meaning, schedule work, retry, or
verify effects.

## Contract

`DetectorInputContext` declares the spatial and identity relationship between
one detector input image and one captured frame:

- `frame_id` and `source_id` identify the observation.
- `root_bounds` are the complete frame-root bounds.
- `roi_root` is the searched region in frame-root coordinates.
- `input_bounds_local` are the bounds of the exact image passed to the
  detector, with origin `(0, 0)`.

The input image may be a direct crop or a resized form of `roi_root`.
`local_rect_to_root()` maps half-open detector-local rectangles to root space.
Leading edges round down and trailing edges round up, ensuring the mapped root
rectangle contains the complete detector result.

`EvidenceAssembler` combines that context with detector output fields:

- evidence identity and kind
- detector-native normalized score
- provenance
- detector-specific result
- optional detector-local bounds and duration

It returns an immutable `Evidence` whose `roi_root` and `bounds_root` use frame
root coordinates.

## Dependency rule

Production Vision code must not import Observation or Evidence. The integration
caller may depend on all three packages and performs the explicit field-level
adaptation:

```python
result = matching_service.match(
    image=prepared_image,
    template_key="ui.submit",
    candidate_floor=0.7,
)

context = DetectorInputContext(
    frame_id=frame.info.frame_id,
    source_id=frame.info.source_id,
    root_bounds=frame.info.root_bounds,
    roi_root=searched_roi_root,
    input_bounds_local=Rect(
        x=0,
        y=0,
        width=prepared_image.shape[1],
        height=prepared_image.shape[0],
    ),
)

evidence = EvidenceAssembler.assemble(
    context=context,
    evidence_id=EvidenceId("template-1"),
    kind=EvidenceKind("template.match"),
    score=candidate.score,
    bounds_local=candidate.rect,
    provenance=provenance,
    result=candidate,
)
```

There is deliberately no adapter from a concrete Vision result type in the
Evidence package. This prevents Evidence from depending on template matching,
OCR, colour, hash, or feature detector implementations.

## Letterbox and screen coordinates

Vision and the bridge do not know whether a frame contains letterboxing. The
caller preparing the detector input chooses the correct `roi_root` and declares
its correspondence with `input_bounds_local`.

Screen conversion remains an Observation or Execution concern. Evidence stores
root coordinates only; it does not carry window placement or screen geometry.
