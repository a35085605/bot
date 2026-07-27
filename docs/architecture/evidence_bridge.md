# Detector Result to Evidence Bridge

## Purpose

The `perception_integration` package contextualizes detector-local output as
frame-root `Evidence` while keeping Observation, Vision primitives, and Evidence
independently usable.

```text
Observation frame + input preparation
                  │
                  ▼
            ImagePlacement
                  │
                  ├──────────────► Vision receives pixels only
                  │                         │
                  │                         ▼
                  │              detector-local result
                  │                         │
                  └──────────────► EvidenceAssembler
                                            │
                                            ▼
                                  Evidence in root space
```

The bridge is a pure conversion boundary. It does not capture frames, run or
select detectors, assign semantic meaning, schedule work, retry, or verify
effects.

## Package boundary

The bridge lives outside Observation, Vision, and Evidence because it is the
only component allowed to depend on the contracts of multiple layers.

```text
observation ───────────────┐
vision ────────────────────┼──► perception_integration
geometry ──────────────────┤
evidence ──────────────────┘
```

Production Vision code must not import Observation, Evidence, window metadata,
or screen-coordinate types. Evidence does not own detector-input preparation or
Vision-specific result types.

## Spatial contract

`ImagePlacement` declares the correspondence between one detector image and one
frame-root ROI:

- `input_bounds_local` are the bounds of the complete image passed to the
  detector, with origin `(0, 0)`.
- `content_bounds_local` are the detector-image pixels derived from the frame.
- `source_bounds_root` are the frame-root pixels represented by
  `content_bounds_local`.

The area in `input_bounds_local` outside `content_bounds_local` is synthetic
padding, such as detector-side letterboxing. Detector results must be fully
contained by `content_bounds_local`; results in padding are rejected instead of
being assigned misleading root coordinates.

The source ROI and detector content may have different sizes. Mapping uses
floor for leading edges and ceil for trailing edges, ensuring the returned
half-open root rectangle contains the complete detector result.

`DetectorInputContext` adds observation identity and complete frame bounds:

- `frame_id` and `source_id` identify the observation.
- `root_bounds` are the complete frame-root bounds.
- `placement.source_bounds_root` must be inside `root_bounds`.

It deliberately contains no pixels, window metadata, screen coordinates,
capture backend, detector implementation, or scheduling policy.

## Example

```python
from perception_integration import (
    DetectorInputContext,
    EvidenceAssembler,
    ImagePlacement,
)

result = matching_service.match(
    image=prepared_image,
    template_key="ui.submit",
    candidate_floor=0.7,
)

input_bounds = Rect(
    x=0,
    y=0,
    width=prepared_image.shape[1],
    height=prepared_image.shape[0],
)

context = DetectorInputContext(
    frame_id=frame.info.frame_id,
    source_id=frame.info.source_id,
    root_bounds=frame.info.root_bounds,
    placement=ImagePlacement(
        input_bounds_local=input_bounds,
        content_bounds_local=detector_content_bounds,
        source_bounds_root=searched_roi_root,
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

For a direct crop or a resize without padding, `content_bounds_local` equals
`input_bounds_local`. For detector-side letterboxing, it describes only the
unpadded content rectangle.

## Screen coordinates

Screen conversion remains an Observation or Execution concern. Evidence stores
root coordinates only; it does not carry window placement, client offsets, DPI
scaling, or screen geometry.
