# Capture, content, and execution boundaries

## Purpose

The content boundary converts a raw capture into clean application pixels and a
stable content-space coordinate context. It does not assign semantic meaning or
choose an action.

```text
CapturedFrame
raw capture-space
      │
      │ ContentRegionLocator
      ▼
CapturedContent
zero-based content-space
      │
      ├────────► optional detector-input / evidence processing
      │
      └────────► caller-owned target selection
                         │
                         ▼
                 ContentPointTarget
                         │
                         │ ExecutionTargetResolver
                         ▼
                 ScreenPoint / DevicePoint
```

## Capture to content

`ContentRegionLocator` answers:

> Which capture-space rectangle represents clean application content?

A locator may use configured geometry, capture dimensions, pixels, or
capture-time source provenance. It returns either `LocatedContentRegion` or
`ContentRegionUnavailable`.

`extract_content()` validates the result, crops the raster, establishes a
zero-based `ContentFrame`, and preserves locator provenance and confidence.
`ContentPlacementInCapture` records which raw-capture rectangle is represented by
content-space.

`ContentFrame` composes the crop offset into capture-time native mappings. These
mappings explain historical pixels; they do not describe current runtime state
and are not execution guarantees.

The content boundary does not:

- resize or normalize detector inputs;
- choose detector regions;
- assign scenes, controls, goals, or other application semantics;
- retain state across frames;
- establish current target availability;
- choose an execution channel; or
- decide whether an interaction should occur.

Detector crop, resize, padding, and normalization remain optional core
capabilities in `detector_input` and `imaging`. Detector implementations are
external packages supplied by the consuming application's composition root.

## Visual target association

A content region is not automatically identical to a logical target. A desktop
capture may contain several windows, and an emulator may expose both host-window
and device channels.

`visual_target_binding` associates historical content with a logical target and
records the evidence for that association. It does not claim that the target or
channel remains available.

## Content to execution

The consuming application chooses an operation target in content-space, such as
`ContentPointTarget`. It should not construct `ScreenPoint` or `DevicePoint`
values from stale capture geometry.

`ExecutionTargetResolver` receives:

- the content-space target;
- the originating `ContentFrame`;
- a fresh `TargetRuntimeSnapshot`;
- the selected control channel; and
- an optional `VisualTargetBinding` when explicit association is required.

The resolver returns either a native `ResolvedExecutionTarget` or
`ExecutionTargetUnavailable`.

A resolver must validate observation identity, bounds, channel readiness,
binding compatibility, and current geometry immediately before a side effect.
If those facts changed incompatibly, resolution fails and the caller decides
whether to reacquire, retry, choose another channel, or stop.

Typical implementations are:

```text
DesktopExecutionTargetResolver
    ContentPointTarget -> ScreenPoint

AdbExecutionTargetResolver
    ContentPointTarget -> DevicePoint
```

This boundary resolves how to perform a selected interaction. It never decides
which interaction is appropriate or whether an application-level goal succeeded.
