Observation
  Frame + window context + coordinate transform
        │
        ▼
Vision primitives
  template / OCR / hash / color / features detection
        │
        ▼
Evidence
  detector result + score + ROI + provenance
        │
        ▼
Semantic perception
  evidence fusion + calibration + recognition
        │
        ▼
World snapshot
  semantic observations for one frame
        │
        ▼
World-state tracking
  temporal stabilization + transitions + memory
        │
        ▼
Decision
  goals + stable state + task memory → intent
        │
        ▼
Execution
  intent → validated input commands → execution report
        │
        ▼
Effect verification
  did the expected state transition occur?
        │
        └──────────────────────► Observation
