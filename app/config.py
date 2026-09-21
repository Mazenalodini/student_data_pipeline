from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[1]
CONFIG_FILE = BASE_DIR / "config.json"


@dataclass(frozen=True)
class SourceConfig:
    csv_path: Path
    api_url: str
    api_timeout_seconds: int
    api_max_retries: int
    api_backoff_seconds: float
    database_path: Path


@dataclass(frozen=True)
class OutputConfig:
    final_dataset: Path
    student_ml_dataset: Path
    rejected_records: Path
    metrics_report: Path
    run_report: Path
    log_file: Path
    api_raw_snapshot: Path
    database_raw_snapshot: Path


@dataclass(frozen=True)
class ProcessingConfig:
    default_mode: str
    missing_value_strategy: dict[str, str]
    minimum_attendance_good: float


@dataclass(frozen=True)
class AppConfig:
    project_name: str
    version: str
    sources: SourceConfig
    output: OutputConfig
    processing: ProcessingConfig


def _path_from_config(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else BASE_DIR / path


def load_config(path: Path = CONFIG_FILE) -> AppConfig:
    raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    sources = raw["sources"]
    output = raw["output"]
    processing = raw["processing"]

    return AppConfig(
        project_name=raw["project"]["name"],
        version=raw["project"]["version"],
        sources=SourceConfig(
            csv_path=_path_from_config(sources["csv"]["path"]),
            api_url=os.getenv("STUDENT_PIPELINE_API_URL", sources["api"]["url"]),
            api_timeout_seconds=int(
                os.getenv(
                    "STUDENT_PIPELINE_API_TIMEOUT",
                    sources["api"]["timeout_seconds"],
                )
            ),
            api_max_retries=int(sources["api"].get("max_retries", 3)),
            api_backoff_seconds=float(sources["api"].get("backoff_seconds", 1.0)),
            database_path=_path_from_config(sources["database"]["path"]),
        ),
        output=OutputConfig(
            final_dataset=_path_from_config(output["final_dataset"]),
            student_ml_dataset=_path_from_config(output["student_ml_dataset"]),
            rejected_records=_path_from_config(output["rejected_records"]),
            metrics_report=_path_from_config(output["metrics_report"]),
            run_report=_path_from_config(output["run_report"]),
            log_file=_path_from_config(output["log_file"]),
            api_raw_snapshot=_path_from_config(output["api_raw_snapshot"]),
            database_raw_snapshot=_path_from_config(output["database_raw_snapshot"]),
        ),
        processing=ProcessingConfig(
            default_mode=processing["default_mode"],
            missing_value_strategy=processing["missing_value_strategy"],
            minimum_attendance_good=float(
                processing["minimum_attendance_good"]
            ),
        ),
    )
