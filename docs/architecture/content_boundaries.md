# Capture, content, and execution boundaries

## Vocabulary

The pipeline uses **content** for the clean application pixels derived from one
raw capture. A viewport may instead mean an application camera, scroll viewport,
or visible panel, so it is not used for this capture boundary.

```text
CapturedFrame                       CapturedContent
raw capture-space                   content-space
      │                                   │
      │ ContentExtractor                  │ Perception
      ▼                                   ▼
CapturedContent                  Evidence / WorldSnapshot
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

`ContentExtractor` derives clean content from the current `CapturedFrame`.
Extraction is tied to that exact capture. An implementation may inspect current
capture dimensions or window metadata on every frame to remove title bars,
window chrome, desktop pixels, or letterbox bars.

A successful extraction returns `CapturedContent`, which contains:

- immutable clean-content pixels;
- a `ContentFrame`;
- `ContentPlacementInCapture`;
- pixel format; and
- extraction provenance and confidence.

`ContentPlacementInCapture` describes the real raw-capture rectangle represented
by content-space. Content-space starts at `(0, 0)` and preserves the selected
rectangle's pixel dimensions.

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
