# Capture, Content, and Target Runtime boundaries

## Three kinds of truth

The framework keeps three time semantics separate:

```text
Capture truth       at frame acquisition
Runtime truth       at the latest target inspection
Execution truth     immediately before a side effect
```

A fact may exist in more than one boundary without being the same claim. For
example, a frame may retain the desktop geometry that explained its pixels at
capture time while Target Runtime reports the window's latest geometry. Neither
snapshot is an execution lock; mutable preconditions are revalidated before
input.

## Capture owns historical pixel provenance

Capture answers:

> What pixels were acquired, from which native source, and how were those pixels
> positioned when this frame was acquired?

A captured frame may retain:

- capture backend and stream identity;
- source or native surface identity;
- capture-time desktop, display, crop, scale, and rotation geometry;
- mappings from frame root-space to native coordinate spaces; and
- pixel integrity and acquisition diagnostics.

These values remain useful after the target moves or disappears because they
explain one immutable historical raster. Capture does not report current focus,
minimized state, process state, ADB readiness, or execution capability.

`root_to_screen` is therefore valid Capture data when it means:

> the mapping from this frame's root-space to the host virtual-screen at
> `captured_at`.

It is optional because an ADB screenshot may map to a device display instead of
the host screen, while an offline image may have no native mapping.

## Content owns clean visual-region derivation

Content answers:

> Which capture-space rectangle is the clean application content for visual
> interpretation?

Content crops the captured raster, establishes content-space at `(0, 0)`, and
composes the crop offset into every capture-time native mapping. It does not own
logical target availability, current channel state, or execution readiness.

```text
CapturedFrame
    │
    │ ContentRegionLocator
    ▼
CapturedContent
    ├── clean raster
    ├── placement in capture
    └── derived capture-time native mappings
```

A capture source and a content region are not necessarily the same thing:

- a desktop capture can contain several target windows;
- a window capture can include title bars or letterboxing;
- an emulator window can contain a device viewport plus host controls; and
- an ADB screenshot can include status and navigation system UI.

## Target Runtime owns current operational state

Target Runtime answers:

> Does the logical target currently exist, and what do its control channels
> currently report?

It owns current target availability, channel identities, readiness, blockers,
window state, ADB state, and current native geometry. It does not interpret
pixels or decide which raster region is clean application content.

A runtime snapshot may guide caller-owned policy, but it can become stale
immediately. Execution must inspect or revalidate mutable channel and geometry
conditions before a side effect.

## Visual target binding joins the branches

Capture and Target Runtime remain independent observations. When a visual region
must be associated with a logical target, orchestration uses the separate
`visual_target_binding` boundary:

```text
CapturedContent + TargetRuntimeSnapshot
                 │
                 ▼
         VisualTargetBinder
                 │
                 ▼
         VisualTargetBinding
```

A binding records the evidence for the historical association, such as:

- a target-scoped capture request;
- matching native window identity;
- matching device and display identity;
- compatible geometry; or
- visual recognition.

The binding does not prove that the target or channel remains available. It is
validated again with fresh Target Runtime state during execution preflight.

## Common capture modes

### Desktop window capture

```text
Capture source: window surface
Native mapping: frame root -> host screen
Content: clean client/application viewport
Runtime: current window state
Execution: validate window identity and current geometry
```

### Full desktop or monitor capture

```text
Capture source: desktop display
Native mapping: frame root -> host screen
Content: one located application region
Binding: content region -> logical target/window channel
Runtime: current target window state
```

### Direct ADB screenshot

```text
Capture source: device display
Native mapping: frame root -> device display
Content: application viewport after optional system-UI removal
Binding: device/display identity -> logical target/ADB channel
Runtime: current ADB and device display state
```

### Emulator or mirroring window with ADB input

This mode may require both mappings:

```text
content -> host screen
content -> device display
```

The first explains desktop pixels. The second supports ADB input. Binding joins
the host surface, device display, logical target, and selected channel without
making Capture or Content own current runtime truth.

## Dependency direction

```text
capture ───────────────► content

capture + content
          └────────────► visual_target_binding ◄──────── target_runtime

content + binding + fresh target_runtime
          └────────────► execution target resolution
```

Capture and Content must not import Target Runtime. Target Runtime must not import
visual pixels or content extraction. The binding layer is the explicit join.
