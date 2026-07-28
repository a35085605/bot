# Canonical viewport compatibility

The clean application pixels derived from a raw capture are now modeled by the
`content` package rather than as a canonical viewport.

See [Capture, content, and execution boundaries](content_boundaries.md) for the
current architecture.

The `viewport` package remains temporarily available as a compatibility layer:

- `CanonicalViewport` delegates to `content.ContentFrame`.
- `ContentPlacement` and `ViewportPlacement` delegate to
  `content.ContentPlacementInCapture`.
- capture-time screen helpers remain only for existing callers; new execution
  code must use `execution.ExecutionTargetResolver`.

New code must not introduce additional dependencies on the viewport names.
