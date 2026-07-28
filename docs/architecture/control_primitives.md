# Control Primitives

## Purpose

The `control` package defines synchronous, backend-neutral contracts for native
input and target preparation. It deliberately stops below planning and
orchestration.

```text
Future orchestration / scheduling
              │
              ▼
        control ports
              │
      ┌───────┴────────┐
      ▼                ▼
Desktop adapters    ADB adapters
(not implemented)   (not implemented)
```

The package does not consume `WorldState`, inspect target runtime, select a
control channel, acquire locks, activate a window implicitly, retry operations,
or verify application effects.

## Capability-oriented ports

Ports are split by independently implementable capability instead of requiring
one monolithic executor:

- `PointerMover`
- `PointerClicker`
- `PointerScroller`
- `PointerDragger`
- `KeyStateController`
- `KeyPresser`
- `KeyChordController`
- `TextController`
- `BackNavigator`
- `WindowActivator`
- `WindowRestorer`

This lets a desktop channel expose activation and pointer movement while an ADB
channel can expose tapping, dragging, key presses, text, and Back without
pretending that it supports window focus.

## Native coordinate spaces

Control primitives accept channel-native coordinates only:

- `ScreenPoint` represents the operating system virtual screen and therefore
  permits negative coordinates for monitors positioned left or above the
  primary display.
- `DevicePoint` represents a device display coordinate and rejects negative
  coordinates.

Conversion from observation root coordinates to either native coordinate space
belongs to a future planning or orchestration boundary. Control ports never
receive `FrameInfo`, `WorldSnapshot`, or semantic control observations.

## Pointer operations

Pointer requests are immutable values:

- `PointerMove`
- `PointerClick`
- `PointerScroll`
- `PointerDrag`

`ScrollDelta` uses semantic steps rather than Windows wheel units, pixels, or
ADB swipe distance. A concrete adapter will define how one step maps to its
native mechanism.

The ports are separated because capabilities differ. For example, an ADB input
adapter may support click-like taps and drag-like swipes without supporting a
persistent pointer position or hover.

## Keyboard and text

Physical key state, key presses, chords, and text entry are separate contracts.
Text entry must not be modeled as a sequence of physical keys because keyboard
layouts, input methods, Unicode support, clipboard strategies, and ADB text
injection have different semantics.

## Window preparation

`WindowActivator` and `WindowRestorer` are optional desktop-oriented
capabilities. They are not prerequisites embedded inside pointer or keyboard
ports. Calling `activate` only reports the result of the platform request; it
does not guarantee that the window remains foreground afterward.

ADB channels do not implement either window port.

## Synchronous result semantics

Every port method is synchronous and returns `ControlOperationResult`. Success
means that the backend completed the requested native operation attempt. It does
not mean that:

- the intended semantic control received the input,
- a scene transition occurred,
- a window remained focused,
- an observation was fresh, or
- the application-level effect succeeded.

Those guarantees belong to future orchestration and effect-verification layers.

## Non-goals

This package intentionally does not provide:

- an execution queue or worker,
- cross-window mutual exclusion,
- target or channel selection,
- focus-before-click composition,
- freshness validation,
- coordinate conversion from observations,
- retries or timeout policy,
- Win32, X11, Wayland, macOS, or ADB adapters,
- execution plans or application-level reports.
