from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from time import perf_counter
from typing import Any


@dataclass
class PipelineMetrics:
    total_records: int = 0
    valid_records: int = 0
    rejected_records: int = 0
    duplicate_records: int = 0
    missing_values_handled: int = 0
    invalid_records: int = 0
    integrated_records: int = 0
    cross_source_mismatches: int = 0
    source_records: dict[str, int] = field(default_factory=dict)
    rejected_by_source: dict[str, int] = field(default_factory=dict)
    rejection_reasons: dict[str, int] = field(default_factory=dict)
    outputs: dict[str, str] = field(default_factory=dict)
    source_hashes: dict[str, str] = field(default_factory=dict)
    processing_mode: str = "full"
    cache_hits: int = 0
    cache_misses: int = 0
    duration_seconds: float = 0.0

    def start_timer(self) -> float:
        return perf_counter()

    def stop_timer(self, started_at: float) -> None:
        self.duration_seconds = round(perf_counter() - started_at, 4)

    def add_rejection(self, source: str, reason: str) -> None:
        self.rejected_records += 1
        self.invalid_records += 1
        self.rejected_by_source[source] = self.rejected_by_source.get(source, 0) + 1
        self.rejection_reasons[reason] = self.rejection_reasons.get(reason, 0) + 1

    def as_dict(self) -> dict[str, Any]:
        return {
            "total_records": self.total_records,
            "valid_records": self.valid_records,
            "rejected_records": self.rejected_records,
            "duplicate_records": self.duplicate_records,
            "missing_values_handled": self.missing_values_handled,
            "invalid_records": self.invalid_records,
            "integrated_records": self.integrated_records,
            "cross_source_mismatches": self.cross_source_mismatches,
            "source_records": self.source_records,
            "rejected_by_source": self.rejected_by_source,
            "rejection_reasons": self.rejection_reasons,
            "outputs": self.outputs,
            "source_hashes": self.source_hashes,
            "processing_mode": self.processing_mode,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "processing_time_seconds": self.duration_seconds,
        }


def save_metrics(metrics: PipelineMetrics, output_file: Path) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(
        json.dumps(metrics.as_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
