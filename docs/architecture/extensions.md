# External extensions

## Purpose

Extension implementations are maintained outside this repository. The interaction
kernel publishes reusable contracts, but it does not vendor, auto-discover,
register, version, or release extension implementations.

A consuming application installs the external packages it needs and wires them
explicitly in its composition root.

## Dependency rule

```text
consumer composition
        │
        ├──────────────► external extensions
        │                         │
        │                         ▼
        └──────────────► public interaction contracts
                          ├── target / control_channel
                          ├── observation.target_runtime
                          ├── desktop_window / adb verticals
                          ├── content and targeting
                          ├── detector_input and evidence
                          ├── execution
                          └── imaging and geometry
```

An external extension may depend on public interaction contracts. Core packages
must not import an extension, and the core must remain usable when every extension
is absent.

## Built-in vertical packages

Window and ADB follow the same ownership pattern expected of external channels:

```text
target / control_channel                 shared interaction kernel
           ▲                                      ▲
           │                                      │
observation.target_runtime               extension observation
           ▲                                      ▲
           │                                      │
desktop_window.observation       adb.observation  custom channel
```

Target Runtime does not import platform packages. Callers import platform-specific
models and inspectors from the vertical package that owns them.

## Control-channel extensions

An external package may add a channel family without editing a core enum, union,
or platform package. It defines its detail model, constructs a stable
`ControlChannelKind`, and implements the generic ports it needs.

```python
from dataclasses import dataclass

from control_channel import ControlChannelKind
from observation.target_runtime import (
    ControlChannelInspector,
    ControlChannelSnapshot,
)

WEB_DRIVER = ControlChannelKind("webdriver")


@dataclass(frozen=True, slots=True)
class WebDriverChannelState:
    session_id: str
    current_url: str | None = None


inspector: ControlChannelInspector[WebDriverChannelState]
snapshot: ControlChannelSnapshot[WebDriverChannelState]
```

The extension owns the relationship between its kind and detail model. Target
Runtime validates shared snapshot invariants but does not register or discover
extension packages.

A mature extension may use:

```text
webdriver_channel/
├── observation/
├── management/
├── execution/
└── adapters/
```

Only the capability families it actually supports are required.

## Composition rules

1. Activation is explicit in the consuming application's composition root.
2. Dependencies use only public interaction contracts.
3. The core never imports or dynamically discovers the extension.
4. Removing or replacing the extension requires no core changes.
5. Extension-to-extension dependencies are explicit and documented.
6. Package-version compatibility is declared by the extension itself.
