# External extensions

## Purpose

Extension implementations are maintained outside this repository. The interaction
kernel publishes reusable contracts, but it does not contain an `extensions/`
source package and does not vendor, auto-discover, register, version, or release
extension implementations.

A consuming application installs the external packages it needs and wires them
explicitly in its own composition root.

```text
consuming application
        │
        ├── policy / state / semantics
        ├── separately installed extension packages
        └── interaction-kernel contracts and adapters
```

## Dependency rule

The dependency direction is one way:

```text
consumer composition
        │
        ├──────────────► external extensions
        │                         │
        │                         ▼
        └──────────────► public interaction contracts
                          ├── observation
                          ├── content and targeting
                          ├── detector_input and evidence
                          ├── execution
                          └── imaging and geometry
```

An external extension may depend on public interaction contracts. Core packages
must not import an extension, and the core must remain usable when every extension
is absent.

## Repository ownership

Extension-specific concerns belong to the repository or package that owns the
extension, including:

- implementation code and optional third-party dependencies;
- domain models and adapter-specific ports that are not core contracts;
- unit and integration tests;
- reference assets or other extension-owned resources;
- documentation, versioning, release notes, and compatibility policy; and
- security updates and deprecation schedules.

This repository may document generic integration boundaries, but it must not
contain extension implementations or extension-specific tests.

## Composition rules

External extensions should follow these rules:

1. activation is explicit in the consuming application's composition root;
2. dependencies on this framework use only public contracts;
3. the core never imports or dynamically discovers the extension;
4. removing or replacing the extension requires no changes to core packages;
5. extension-to-extension dependencies are explicit and documented; and
6. package-version compatibility is declared by the extension itself.

## Migration from bundled extensions

Earlier revisions of this repository bundled a vision implementation under
`extensions.vision`, including reference-asset and template-matching capabilities.
That implementation and its tests are no longer part of this repository.

Consumers that relied on `extensions.vision.*` must move or install that
implementation from a separately maintained package and update their imports
before upgrading. The core does not provide a compatibility facade or an official
external package location.
