# Fixed viewport ROI detector input preparation

## Purpose

A detector should receive pixels and detector-local coordinates. It should not
know how a canonical viewport was captured, which scene selected a region, or
how detector results later become semantic evidence.

This boundary prepares a detector image from an already resolved canonical
viewport-root ROI:

```text
Canonical viewport pixels + viewport-root ROI + requested output size
                              │
                              ▼
                       detector_input
                              │
                    crop through imaging
                              │
                    resize through imaging
                              │
                              ▼
                 PreparedDetectorInput
                 ├── RasterImage
                 └── DetectorInputContext
                              │
             ┌────────────────┴────────────────┐
             ▼                                 ▼
     Vision receives pixels          Evidence bridge receives
                                     placement and observation ID
```

## Ownership

### `imaging`

The top-level `imaging` package owns general raster operations:

- immutable `RasterImage`
- image-local crop
- interpolation selection
- the `ImageResizer` capability
- the OpenCV resize adapter

It does not import Observation, Perception, Vision, Evidence, or World Model.
It assigns no scene, control, template, or color-order meaning to pixels.

### `detector_input`

The top-level `detector_input` package owns detector invocation input:

- `ImagePlacement`
- `DetectorInputContext`
- `PreparedDetectorInput`
- `PreparationProvenance`
- `FixedViewportRoiPreparer`

It combines general imaging operations with observation identity and canonical
viewport-root placement. It does not choose an ROI or detector.

### Perception planning

Perception planning is responsible for deciding what resolved viewport-root ROI
to inspect and what detector input size to request. It does not implement pixel
crop, resize, or affine warping.

## Fixed ROI contract

`FixedViewportRoiPreparer` requires:

- frame and source identity
- complete canonical viewport-root bounds
- a raster whose dimensions equal those root bounds
- a resolved ROI contained by the root bounds
- an output size
- an interpolation method

The preparer crops the ROI and resizes it only when its source and output sizes
differ.

For this version there is no padding, therefore:

```text
input_bounds_local == content_bounds_local
```

The placement records:

```text
detector-local content --scale/translation--> canonical viewport-root ROI
```

The complete detector input maps exactly back to the requested ROI, even when
the two rectangles have different dimensions.

## Example

```python
from detector_input import FixedViewportRoiPreparer
from geometry.rect import Rect
from geometry.size import Size
from imaging import Interpolation, RasterImage
from imaging.adapters import OpenCVImageResizer

source = RasterImage(pixels=perception_viewport.pixels)
prepared = FixedViewportRoiPreparer(
    resizer=OpenCVImageResizer(),
).prepare(
    frame_id=perception_viewport.frame_id,
    source_id=perception_viewport.source_id,
    root_bounds=perception_viewport.root_bounds,
    image=source,
    roi_root=Rect(x=1200, y=675, width=267, height=150),
    output_size=Size(width=320, height=180),
    interpolation=Interpolation.LINEAR,
)

candidate = matching_service.match(
    image=prepared.pixels,
    template_key="template.login_button_active",
    candidate_floor=0.7,
)

evidence = EvidenceAssembler.assemble(
    context=prepared.context,
    bounds_local=candidate.rect,
    # evidence identity, score, provenance, and result omitted
)
```

Vision receives only `prepared.pixels` and the template. It does not know the
source ROI, viewport resolution, or resize history.

## Non-goals

This version does not provide:

- reference-resolution ROI registration
- template authoring metadata
- anchor-relative or local-of-local ROI resolution
- padding or letterboxing
- rotation, shear, perspective, or arbitrary affine image warping
- detector scheduling or dependency graphs

General coordinate transforms belong in `geometry`; pixel warping belongs in
`imaging`. A future affine-warp PR should preserve that split rather than adding
those operations to Perception.
