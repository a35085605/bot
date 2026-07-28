# Perception viewport compatibility

Perception no longer owns the clean-content extraction boundary.

See [Capture, content, and execution boundaries](content_boundaries.md) for the
current architecture.

New orchestration uses:

```python
content = extract_content(capture, extractor=content_extractor)
```

Perception consumes `CapturedContent`; it does not consume `CapturedFrame` and
it does not create the clean-content region.

`perception_integration.viewport` remains temporarily available for callers
using `extract_viewport`, `PerceptionViewport`, and the previous extractor
names. Those APIs delegate to `content` and should not be used by new code.
