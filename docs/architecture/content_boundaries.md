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

A locator may inspect current capture dimensions, window metadata, configured
geometry, or pixels on every frame to identify the region that excludes title
bars, window chrome, desktop pixels, or letterbox bars. It returns either
`LocatedContentRegion` or `ContentRegionUnavailable`.

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

This boundary does not:

- resize or normalize pixels;
- select detector ROIs;
- run detectors;
- assign semantic meaning;
- choose a control channel; or
- resolve screen or device coordinates.

Detector crop, resize, padding, and normalization remain in `detector_input` and
`imaging`.

## Boundary two: content to execution

Decision and planning produce targets in content-space, such as
`ContentPointTarget`. They do not create `ScreenPoint` or `DevicePoint` values.

`ExecutionTargetResolver` receives:

- the content-space target;
- the originating `ContentFrame`;
- a fresh `TargetRuntimeSnapshot`; and
- the selected control channel.

It returns either a native `ResolvedExecutionTarget` or
`ExecutionTargetUnavailable`.

A resolver must validate observation identity, content bounds, channel
readiness, and current geometry immediately before a side effect. Capture-time
geometry is provenance, not a lock or execution guarantee. If the window,
device, orientation, display geometry, or source identity changed incompatibly,
the resolver should fail and allow orchestration to capture and perceive again.

Typical implementations are:

```text
DesktopExecutionTargetResolver
    ContentPointTarget -> ScreenPoint

AdbExecutionTargetResolver
    ContentPointTarget -> DevicePoint
```

## World model bridge

`ContentFrame.frame` supplies the current world model with content-root bounds
and a derived content-root-to-screen transform. This bridge preserves the
existing world snapshot contract; it is not a substitute for execution-time
runtime inspection and target resolution.
