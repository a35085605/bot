Observation coordination
  Capture + Target Runtime + Temporal snapshots
        │
        ├───────────────┐
        │               │
        ▼               ▼
Visual Capture      Runtime / time policy
  pixels + geometry   focus + readiness + date/time
        │               │
        ▼               │
Vision primitives      │
  template / OCR / hash / color / features detection
        │               │
        ▼               │
Evidence                │
  detector result + score + ROI + provenance
        │               │
        ▼               │
Semantic perception     │
  evidence fusion + calibration + recognition
        │               │
        ▼               │
World snapshot          │
  semantic observations for one frame
        │               │
        ▼               │
World-state tracking    │
  temporal stabilization + transitions + memory
        │               │
        └───────┬───────┘
                ▼
Decision
  goals + stable state + runtime + temporal policy → intent
        │
        ▼
Execution
  intent → revalidated input commands → execution report
        │
        ▼
Effect verification
  did the expected state transition occur?
        │
        └──────────────────────► Observation coordination

See [`docs/architecture/observation_boundaries.md`](docs/architecture/observation_boundaries.md)
for the Capture, Target Runtime, Temporal, and coordination boundaries.
