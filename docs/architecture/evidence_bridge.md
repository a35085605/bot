# Detector Result to Evidence Bridge

## Purpose

`detector_input` prepares one detector invocation and records its spatial
context. `perception_integration` then converts detector-local output into
content-root `Evidence`.

```text
Content image + resolved content ROI
                 │
                 ▼
         detector_input preparation
                 │
                 ├──────────────► external detector receives pixels only
                 │                         │
                 │                         ▼
                 │              detector-local result
                 │                         │
                 └──────────────► EvidenceAssembler
                                           │
                                           ▼
                               Evidence in content-root
```

The bridge is a pure conversion boundary. It does not capture frames, crop or
resize images, run or select detectors, assign semantic meaning, schedule work,
retry, or verify effects.

## Package boundaries

```text
geometry ───────────────► imaging
                              │
observation ───────┐           ▼
geometry ──────────┼──► detector_input ──► external detector packages
imaging ───────────┘           │
                              ▼
evidence ─────────────► perception_integration
```

- `imaging` owns immutable rasters, crop, resize capability, and concrete image
  adapters.
- `detector_input` owns prepared images, placements, and invocation identity.
- external detector packages may consume prepared pixels without becoming core
  dependencies.
- `perception_integration` owns only detector-result-to-Evidence conversion.

Callers import detector-input contracts directly from `detector_input` and the
bridge from `perception_integration`. Detector implementations are installed
separately and supplied by the consuming application's composition root.

External detector packages must not require Observation, window metadata, or
screen-coordinate types merely to run a detector. Evidence does not own
detector-input preparation or extension-specific result types.

## Spatial contract

`ImagePlacement` declares the correspondence between one detector image and one
content-root ROI:

- `input_bounds_local` are the bounds of the complete image passed to the
  detector, with origin `(0, 0)`;
- `content_bounds_local` are the detector-image pixels derived from the source;
  and
- `source_bounds_root` are the content-root pixels represented by
  `content_bounds_local`.

The area in `input_bounds_local` outside `content_bounds_local` is synthetic
padding, such as detector-side letterboxing. Detector results must be fully
contained by `content_bounds_local`; results in padding are rejected instead of
being assigned misleading root coordinates.

The source ROI and detector content may have different sizes. Mapping uses
floor for leading edges and ceil for trailing edges, ensuring the returned
half-open root rectangle contains the complete detector result.

`DetectorInputContext` adds observation identity and complete content bounds:

- `frame_id` and `source_id` identify the observation;
- `root_bounds` are the complete content-root bounds; and
- `placement.source_bounds_root` must be inside `root_bounds`.

It deliberately contains no pixels, window metadata, screen coordinates,
capture backend, detector implementation, or scheduling policy.

## Example

```python
from detector_input import FixedViewportRoiPreparer
from geometry.rect import Rect
from geometry.size import Size
from imaging import Interpolation
from imaging.adapters import OpenCVImageResizer
from perception_integration import EvidenceAssembler

prepared = FixedViewportRoiPreparer(
    resizer=OpenCVImageResizer(),
).prepare(
    frame_id=captured_content.frame_id,
    source_id=captured_content.source_id,
    root_bounds=captured_content.bounds_content,
    image=captured_content.image,
    roi_root=Rect(x=1200, y=675, width=267, height=150),
    output_size=Size(width=320, height=180),
    interpolation=Interpolation.LINEAR,
)

result = detector.detect(prepared.pixels)

evidence = EvidenceAssembler.assemble(
    context=prepared.context,
    evidence_id=EvidenceId("detector-1"),
    kind=EvidenceKind("detector.result"),
    score=result.score,
    bounds_local=result.rect,
    provenance=provenance,
    result=result,
)
```

The concrete `detector` above is supplied by the consumer and may come from any
separately maintained package that obeys the spatial contract.

For a direct crop or a resize without padding, `content_bounds_local` equals
`input_bounds_local`. Future detector-side letterboxing may describe only the
unpadded content rectangle.

## Screen coordinates

Screen conversion remains an Execution concern. Evidence stores content-root
coordinates only; it does not carry window placement, client offsets, DPI
scaling, or screen geometry.

See [`extensions.md`](extensions.md) for external extension dependency rules.
