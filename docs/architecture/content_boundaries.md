# Capture, content, and execution boundaries

## Vocabulary

The pipeline uses **content** for the clean application pixels derived from one
raw capture. A viewport may instead mean an application camera, scroll viewport,
or visible panel, so it is not used for this capture boundary.

```text
CapturedFrame
raw capture-space
      │
      │ ContentRegionLocator
      ▼
LocatedContentRegion
      │
      │ extract_content()
      ▼
CapturedContent
content-space
      │
      │ Perception
      ▼
Evidence / WorldSnapshot
      │
      │ Decision
      ▼
ContentPointTarget
      │
      │ ExecutionTargetResolver
      ▼
ScreenPoint / DevicePoint
```

## Boundary one: capture to content

`ContentRegionLocator` answers one variable question for the current
`CapturedFrame`:

> Which capture-space rectangle represents clean application content?

A locator may inspect current capture dimensions, configured geometry, pixels,
or capture-time source provenance to identify the region that excludes title
bars, window chrome, desktop pixels, emulator controls, system UI, or letterbox
bars. It returns either `LocatedContentRegion` or `ContentRegionUnavailable`.

`extract_content()` is the stable facade around that strategy. It:

- rejects unusable captures before invoking the locator;
- validates the located rectangle against capture bounds;
- converts capture-space bounds to image-local bounds;
- creates a zero-copy crop with `crop_image()` when needed;
- establishes `ContentPlacementInCapture` and `ContentFrame`; and
- constructs validated `CapturedContent`.

This keeps region-selection policy behind the protocol while centralizing crop,
coordinate, provenance, confidence, and failure handling.

A successful extraction returns `CapturedContent`, which contains:

- immutable clean-content pixels;
- a `ContentFrame`;
- `ContentPlacementInCapture`;
- pixel format; and
- locator provenance and confidence.

`ContentPlacementInCapture` describes the real raw-capture rectangle represented
by content-space. Content-space starts at `(0, 0)` and preserves the selected
rectangle's pixel dimensions.

Content crops remain logical zero-copy `RasterImage` views backed by the owned
`CapturedFrame` raster. Unlike the capture acquisition boundary, content
extraction does not require another materialization step.

`ContentFrame` composes the crop offset into every capture-time native coordinate
mapping. A desktop capture may therefore retain content-to-screen provenance,
while an ADB capture may retain content-to-device-display provenance. These are
historical mappings that explain the captured pixels; they are not current
runtime geometry or execution guarantees.

This boundary does not:

- resize or normalize pixels;
- select detector ROIs;
- run detectors;
- assign semantic meaning;
- establish current target availability;
- choose a control channel; or
- claim that a native mapping is still valid for input.

Detector crop, resize, padding, and normalization remain in `detector_input` and
`imaging`.

## Visual target association

A content region is not automatically identical to a logical target. This is
especially important when a capture contains multiple windows, an emulator
window contains both host controls and a device viewport, or one logical target
has desktop and ADB channels.

The separate `visual_target_binding` boundary associates `CapturedContent` with
a `TargetRuntimeSnapshot`. It records why the historical visual region was
associated with a logical target without making Content depend on Target Runtime
or claiming current channel readiness.

## Boundary two: content to execution

Decision and planning produce targets in content-space, such as
`ContentPointTarget`. They do not create `ScreenPoint` or `DevicePoint` values.

`ExecutionTargetResolver` receives:

- the content-space target;
- the originating `ContentFrame`;
- a fresh `TargetRuntimeSnapshot`; and
- the selected control channel.

When the capture source is broader than one logical target, orchestration also
establishes a `VisualTargetBinding` and the resolver validates that association
against the fresh runtime state.

The resolver returns either a native `ResolvedExecutionTarget` or
`ExecutionTargetUnavailable`.

A resolver must validate observation identity, content bounds, channel
readiness, binding compatibility, and current geometry immediately before a side
effect. Capture-time geometry is provenance, not a lock or execution guarantee.
If the window, device, orientation, display geometry, or source identity changed
incompatibly, the resolver should fail and allow orchestration to capture and
perceive again.

Typical implementations are:

```text
DesktopExecutionTargetResolver
    ContentPointTarget -> ScreenPoint

AdbExecutionTargetResolver
    ContentPointTarget -> DevicePoint
```

## World model bridge

`ContentFrame.frame` supplies the current world model with content-root bounds and
derived capture-time native mappings. This bridge preserves the existing world
snapshot contract; it is not a substitute for target binding, execution-time
runtime inspection, or target resolution.
