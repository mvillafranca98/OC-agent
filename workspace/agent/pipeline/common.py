from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class PipelineRun:
    output_path: Path
    rows_written: int
    searches_executed: int
    insufficient_evidence: int
    action_counts: dict[str, int]
    rate_wait_events: int
    rate_wait_seconds: float
    cooldown_events: int

