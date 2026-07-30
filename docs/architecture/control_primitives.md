# Control primitives moved to Execution

The native control contracts now belong to the `execution` boundary because they
produce external side effects.

See [`execution_capabilities.md`](execution_capabilities.md) for lifecycle,
window-management, input, shared result, target-resolution, and effect-verification
boundaries.

The top-level `control` Python package remains only as a temporary compatibility
facade. New code should import the canonical contracts from `execution`.
