# Bot architecture

The agent does not treat visual capture as the root of every decision.
`Capture`, `Target Runtime`, and `Temporal` are independent observation
boundaries that acquire different facts from the external world.

```text
External world
├── Capture
│   └── pixels + capture geometry + integrity + provenance
├── Target Runtime
│   └── target availability + window / ADB channel state + readiness
└── Temporal
    └── wall-clock date/time + monotonic time
            │
            ▼
    Observation coordination
    independently timestamped snapshots for one orchestration cycle
            │
            ├──────────────── visual path ────────────────┐
            │                                             │
            ▼                                             │
         Content                                          │
         clean content raster + coordinate context        │
            │                                             │
            ▼                                             │
      Vision primitives                                   │
      template / OCR / hash / color / feature detection   │
            │                                             │
            ▼                                             │
         Evidence                                         │
         detector result + score + ROI + provenance       │
            │                                             │
            ▼                                             │
    Semantic perception                                   │
    evidence fusion + recognition                         │
            │                                             │
            ▼                                             │
       World snapshot                                     │
       semantic observations for one frame                │
            │                                             │
            ▼                                             │
    World-state tracking                                  │
    stabilization + transitions + memory                  │
            │                                             │
            └──────────────────┬──────────────────────────┘
                               ▼
                            Decision
      goals + stable semantic state + runtime + temporal policy → intent
                               │
                               ▼
                            Execution
      intent → revalidated target and input commands → execution report
                               │
                               ▼
                       Effect verification
                did the expected state transition occur?
                               │
                               └────────► next observation cycle
```

The visual path is optional. For example, a runtime observation may report that
the target application is missing, allowing Decision to produce a launch intent
without acquiring or interpreting a frame.

See [`docs/architecture/observation_boundaries.md`](docs/architecture/observation_boundaries.md)
for the observation families, coordination model, freshness rules, and dependency
direction.

See [`docs/architecture/capture_target_boundaries.md`](docs/architecture/capture_target_boundaries.md)
for the separation between capture-time pixel provenance, clean content,
visual-target binding, current Target Runtime state, and execution preflight.
