"""Contracts for administering control channels and host infrastructure.

Management operations intentionally change channel or host state through
preparation, recovery, configuration, suspension, or shutdown. Observation
remains read-only, while caller-owned orchestration decides when a management
operation is appropriate and verifies its effect through fresh observation.
"""
