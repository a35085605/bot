# Fixed viewport ROI detector input preparation

## Purpose

A detector should receive pixels and detector-local coordinates. It should not
know how content was captured, why a caller selected a region, or how results
will be interpreted.

```text
Content pixels + content-root ROI + requested output size
                         │
                         ▼
                  detector_input
                         │
                crop / optional resize
                         │
                         ▼
             PreparedDetectorInput
             ├── RasterImage
             └── DetectorInputContext
                         │
          ┌──────────────┴──────────────┐
          ▼                             ▼
 external detector package      optional result bridge receives
 receives pixels                placement and observation identity
```

## Ownership

### `imaging`

`imaging` owns immutable raster values, crop, materialization, interpolation,
resize capability, and concrete image adapters. It does not assign application
or detector meaning to pixels.

### `detector_input`

`detector_input` owns the prepared raster and the coordinate correspondence for
one detector invocation:

- `ImagePlacement`;
- `DetectorInputContext`;
- `PreparedDetectorInput`;
- `PreparationProvenance`; and
- `FixedViewportRoiPreparer`.

It does not choose an ROI, select a detector, interpret results, retain state, or
schedule work.

### Caller or external extension planning

The consuming application or an external sensing extension chooses which
content-root ROI to inspect and which detector input size to request. That policy
is intentionally outside this package. No detector extension is bundled in this
repository; separately maintained packages may consume the same prepared-input
contracts.

## Fixed ROI contract

`FixedViewportRoiPreparer` requires frame and source identity, complete
content-root bounds, a matching raster, a contained ROI, an output size, and an
interpolation method.

The preparer crops the ROI and resizes only when the source and output sizes
differ. For this version there is no padding, therefore:

```text
input_bounds_local == content_bounds_local
```

`ImagePlacement` records the mapping from detector-local content back to the
selected content-root ROI. Detector output can therefore be translated without
giving the detector capture, window, device, or execution knowledge.

## Non-goals

This package does not provide:

- scene, control, goal, or workflow semantics;
- detector selection or scheduling;
- cross-frame state or memory;
- reference-resolution ROI registration;
- anchor-relative ROI resolution;
- padding or letterboxing; or
- rotation, shear, perspective, or arbitrary affine warping.

General coordinate transforms belong in `geometry`; pixel warping belongs in
`imaging`; interpretation and policy belong to the consuming application.

See [`extensions.md`](extensions.md) for the external extension boundary.
