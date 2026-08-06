"""Contracts for preparing and maintaining external control channels.

Management operations intentionally change channel or host state so that later
execution can proceed. Observation remains read-only, while caller-owned
orchestration decides when preparation or recovery is appropriate.
"""
