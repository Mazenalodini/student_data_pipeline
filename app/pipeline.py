from __future__ import annotations

import argparse
import json
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from app.config import BASE_DIR, AppConfig, load_config
from app.models import RejectedRecord
from app.output.csv_writer import write_dataframe, write_json, write_rejected_records
from app.sources.api_source import APIExtractionError, clean_and_validate_api, extract_api
from app.sources.csv_source import clean_and_validate_csv, extract_csv
from app.sources.database_source import extract_enrollments, validate_enrollments
from app.transformation.integration import integrate_sources
from app.transformation.transformer import add_derived_columns, build_student_ml_dataset
from app.utils.hashing import sha256_file, sha256_text
from app.utils.logger import configure_logging
from app.utils.metrics import PipelineMetrics, save_metrics
from app.validation.quality import validate_final_dataset

STATE_FILE = BASE_DIR / "state" / "source_manifest.json"
CACHE_DIR = BASE_DIR / "state" / "cache"


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )


def _record_rejections(metrics: PipelineMetrics, records: list[RejectedRecord]) -> None:
    for record in records:
        metrics.add_rejection(record.source, record.error_reason)


def _api_url_fingerprint(url: str) -> str:
    return sha256_text(url)


def _write_cache(
    name: str,
    dataframe: pd.DataFrame,
    rejected: list[RejectedRecord],
) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(CACHE_DIR / f"{name}_valid.csv", index=False)
    _save_json(
        CACHE_DIR / f"{name}_rejected.json",
        [record.as_dict() for record in rejected],
    )


def _read_cache(
    name: str,
) -> tuple[pd.DataFrame, list[RejectedRecord]] | None:
    dataframe_path = CACHE_DIR / f"{name}_valid.csv"
    rejected_path = CACHE_DIR / f"{name}_rejected.json"
    if not dataframe_path.exists() or not rejected_path.exists():
        return None

    dataframe = pd.read_csv(dataframe_path)
    rejected = [
        RejectedRecord(**payload)
        for payload in _load_json(rejected_path, [])
    ]
    return dataframe, rejected


def _write_api_raw_snapshot(dataframe: pd.DataFrame, output_file: Path) -> None:
    records = json.loads(
        dataframe.to_json(
            orient="records",
            date_format="iso",
        )
    )
    write_json(records, output_file)


def _write_database_raw_snapshot(dataframe: pd.DataFrame, output_file: Path) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(output_file, index=False)


def _write_run_report(
    config: AppConfig,
    metrics: PipelineMetrics,
    run_id: str,
) -> None:
    lines = [
        "# Pipeline Run Report",
        "",
        f"Run ID: `{run_id}`",
        f"Generated at (UTC): `{datetime.now(timezone.utc).isoformat()}`",
        "",
        "## Execution Summary",
        "",
        f"- Processing mode: **{metrics.processing_mode}**",
        f"- CSV records: **{metrics.source_records.get('CSV', 0)}**",
        f"- API records: **{metrics.source_records.get('API', 0)}**",
        f"- Database records: **{metrics.source_records.get('DATABASE', 0)}**",
        f"- Integrated records: **{metrics.integrated_records}**",
        f"- Valid final records: **{metrics.valid_records}**",
        f"- Rejected records: **{metrics.rejected_records}**",
        f"- Duplicate records: **{metrics.duplicate_records}**",
        f"- Missing values handled: **{metrics.missing_values_handled}**",
        f"- Cross-source mismatches: **{metrics.cross_source_mismatches}**",
        f"- Processing time: **{metrics.duration_seconds:.4f} seconds**",
        f"- Cache hits: **{metrics.cache_hits}**",
        f"- Cache misses: **{metrics.cache_misses}**",
        "",
        "## Outputs",
        "",
    ]

    for name, path in metrics.outputs.items():
        lines.append(f"- {name}: `{path}`")

    lines.extend(["", "## Rejection Reasons", ""])
    if metrics.rejection_reasons:
        for reason, count in sorted(metrics.rejection_reasons.items()):
            lines.append(f"- {reason}: {count}")
    else:
        lines.append("- None")

    config.output.run_report.parent.mkdir(parents=True, exist_ok=True)
    config.output.run_report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _config_fingerprint(config: AppConfig) -> str:
    payload = {
        "api_url": config.sources.api_url,
        "api_timeout": config.sources.api_timeout_seconds,
        "api_max_retries": config.sources.api_max_retries,
        "api_backoff_seconds": config.sources.api_backoff_seconds,
        "missing_value_strategy": config.processing.missing_value_strategy,
        "minimum_attendance_good": config.processing.minimum_attendance_good,
    }
    return sha256_text(json.dumps(payload, sort_keys=True))


def _outputs_exist(config: AppConfig) -> bool:
    return all(
        path.exists()
        for path in [
            config.output.final_dataset,
            config.output.student_ml_dataset,
            config.output.rejected_records,
            config.output.metrics_report,
        ]
    )


def _reuse_previous_run(
    config: AppConfig,
    previous_metrics: dict[str, Any],
    current_hashes: dict[str, str],
    run_id: str,
    started_at: float,
) -> PipelineMetrics:
    metrics = PipelineMetrics(processing_mode="incremental")
    metrics.cache_hits = 3
    metrics.source_hashes = current_hashes
    metrics.source_records = previous_metrics.get("source_records", {})
    metrics.integrated_records = previous_metrics.get("integrated_records", 0)
    metrics.valid_records = previous_metrics.get("valid_records", 0)
    metrics.rejected_records = previous_metrics.get("rejected_records", 0)
    metrics.duplicate_records = previous_metrics.get("duplicate_records", 0)
    metrics.missing_values_handled = previous_metrics.get("missing_values_handled", 0)
    metrics.invalid_records = previous_metrics.get("invalid_records", 0)
    metrics.cross_source_mismatches = previous_metrics.get("cross_source_mismatches", 0)
    metrics.rejected_by_source = previous_metrics.get("rejected_by_source", {})
    metrics.rejection_reasons = previous_metrics.get("rejection_reasons", {})
    metrics.outputs = previous_metrics.get("outputs", {})
    metrics.total_records = previous_metrics.get("total_records", 0)
    metrics.stop_timer(started_at)
    save_metrics(metrics, config.output.metrics_report)
    _write_run_report(config, metrics, run_id)
    return metrics


def run_pipeline(config: AppConfig, mode: str | None = None) -> PipelineMetrics:
    selected_mode = mode or config.processing.default_mode
    if selected_mode not in {"full", "incremental"}:
        raise ValueError("mode must be either 'full' or 'incremental'")

    logger = configure_logging(config.output.log_file)
    metrics = PipelineMetrics(processing_mode=selected_mode)
    started_at = metrics.start_timer()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    config_hash = _config_fingerprint(config)

    logger.info("Pipeline started | run_id=%s | mode=%s", run_id, selected_mode)

    csv_hash = sha256_file(config.sources.csv_path)
    database_hash = sha256_file(config.sources.database_path)
    api_endpoint_hash = _api_url_fingerprint(config.sources.api_url)
    previous_manifest = _load_json(STATE_FILE, {})

    # The remote API must still be contacted in incremental mode because an endpoint
    # can change its payload without changing its URL.
    logger.info("REST API extraction started")
    try:
        api_raw, api_payload_hash = extract_api(
            config.sources.api_url,
            timeout=config.sources.api_timeout_seconds,
            max_retries=config.sources.api_max_retries,
            backoff_seconds=config.sources.api_backoff_seconds,
        )
    except APIExtractionError:
        logger.exception("REST API extraction failed")
        raise

    current_hashes = {
        "csv": csv_hash,
        "database": database_hash,
        "api_endpoint": api_endpoint_hash,
        "api_payload": api_payload_hash,
    }

    if (
        selected_mode == "incremental"
        and previous_manifest.get("config_hash") == config_hash
        and previous_manifest.get("source_hashes") == current_hashes
        and _outputs_exist(config)
    ):
        logger.info("No source changes detected; reusing previous pipeline outputs.")
        return _reuse_previous_run(
            config,
            _load_json(config.output.metrics_report, {}),
            current_hashes,
            run_id,
            started_at,
        )

    # CSV: reuse validated cache when only other sources changed.
    previous_csv_hash = previous_manifest.get("source_hashes", {}).get("csv")
    csv_cache = _read_cache("csv") if selected_mode == "incremental" else None
    csv_unchanged = (
        selected_mode == "incremental"
        and previous_csv_hash == csv_hash
        and csv_cache is not None
    )
    if csv_unchanged:
        csv_valid, csv_rejected = csv_cache
        metrics.cache_hits += 1
        metrics.source_records["CSV"] = len(csv_valid) + len(csv_rejected)
        logger.info("CSV source unchanged; reused validated cache.")
    else:
        logger.info("CSV extraction started")
        csv_raw = extract_csv(config.sources.csv_path)
        metrics.source_records["CSV"] = len(csv_raw)
        csv_valid, csv_rejected, csv_stats = clean_and_validate_csv(csv_raw)
        metrics.duplicate_records += (
            csv_stats["exact_duplicates"] + csv_stats["duplicate_student_ids"]
        )
        metrics.missing_values_handled += csv_stats["missing_values_handled"]
        _write_cache("csv", csv_valid, csv_rejected)
        logger.info("CSV records extracted: %s", len(csv_raw))
    _record_rejections(metrics, csv_rejected)

    # API: reuse validated cache when the remote payload has not changed.
    previous_api_hash = previous_manifest.get("source_hashes", {}).get("api_payload")
    api_cache = _read_cache("api") if selected_mode == "incremental" else None
    api_unchanged = (
        selected_mode == "incremental"
        and previous_api_hash == api_payload_hash
        and api_cache is not None
    )
    if api_unchanged:
        api_valid, api_rejected = api_cache
        metrics.cache_hits += 1
        metrics.source_records["API"] = len(api_valid) + len(api_rejected)
        logger.info("REST API payload unchanged; reused validated cache.")
    else:
        metrics.source_records["API"] = len(api_raw)
        _write_api_raw_snapshot(api_raw, config.output.api_raw_snapshot)
        api_valid, api_rejected, api_stats = clean_and_validate_api(api_raw)
        metrics.duplicate_records += (
            api_stats["exact_duplicates"] + api_stats["duplicate_student_ids"]
        )
        metrics.missing_values_handled += api_stats["missing_values_handled"]
        _write_cache("api", api_valid, api_rejected)
        logger.info("API records received: %s", len(api_raw))
    _record_rejections(metrics, api_rejected)

    # SQLite: reuse validated cache when the database has not changed.
    previous_db_hash = previous_manifest.get("source_hashes", {}).get("database")
    db_cache = _read_cache("database") if selected_mode == "incremental" else None
    db_unchanged = (
        selected_mode == "incremental"
        and previous_db_hash == database_hash
        and db_cache is not None
    )
    if db_unchanged:
        database_valid, database_rejected = db_cache
        metrics.cache_hits += 1
        metrics.source_records["DATABASE"] = len(database_valid) + len(database_rejected)
        logger.info("SQLite source unchanged; reused validated cache.")
    else:
        logger.info("SQLite extraction started")
        database_raw = extract_enrollments(config.sources.database_path)
        metrics.source_records["DATABASE"] = len(database_raw)
        _write_database_raw_snapshot(
            database_raw,
            config.output.database_raw_snapshot,
        )
        database_valid, database_rejected, database_stats = validate_enrollments(
            database_raw
        )
        metrics.duplicate_records += (
            database_stats["exact_duplicates"]
            + database_stats["duplicate_enrollments"]
        )
        metrics.missing_values_handled += database_stats["missing_values_handled"]
        _write_cache("database", database_valid, database_rejected)
        logger.info("Database records extracted: %s", len(database_raw))
    _record_rejections(metrics, database_rejected)

    # Integration
    logger.info("Data integration started")
    integrated, integration_rejected = integrate_sources(
        csv_valid,
        api_valid,
        database_valid,
    )
    _record_rejections(metrics, integration_rejected)
    metrics.cross_source_mismatches = len(integration_rejected)
    metrics.integrated_records = len(integrated)

    if integrated.empty:
        raise ValueError("Integration produced no compatible records.")

    # Transformation
    logger.info("Transformation started")
    integrated = add_derived_columns(
        integrated,
        minimum_good_attendance=config.processing.minimum_attendance_good,
    )
    integrated = integrated.sort_values(
        ["student_id", "course_id", "semester"]
    ).reset_index(drop=True)

    # Final validation
    logger.info("Final validation started")
    validation = validate_final_dataset(integrated)
    if not validation.valid:
        raise ValueError(
            "Final dataset validation failed: " + "; ".join(validation.errors)
        )

    metrics.valid_records = len(integrated)
    metrics.total_records = sum(metrics.source_records.values())

    # Load
    write_dataframe(integrated, config.output.final_dataset)
    student_ml_dataset = build_student_ml_dataset(integrated)
    write_dataframe(student_ml_dataset, config.output.student_ml_dataset)

    all_rejected = [
        *csv_rejected,
        *api_rejected,
        *database_rejected,
        *integration_rejected,
    ]
    write_rejected_records(all_rejected, config.output.rejected_records)

    metrics.source_hashes = current_hashes
    metrics.outputs = {
        "final_dataset": str(config.output.final_dataset.relative_to(BASE_DIR)),
        "student_ml_dataset": str(
            config.output.student_ml_dataset.relative_to(BASE_DIR)
        ),
        "rejected_records": str(
            config.output.rejected_records.relative_to(BASE_DIR)
        ),
        "metrics_report": str(config.output.metrics_report.relative_to(BASE_DIR)),
        "run_report": str(config.output.run_report.relative_to(BASE_DIR)),
        "log_file": str(config.output.log_file.relative_to(BASE_DIR)),
        "api_raw_snapshot": str(
            config.output.api_raw_snapshot.relative_to(BASE_DIR)
        ),
        "database_raw_snapshot": str(
            config.output.database_raw_snapshot.relative_to(BASE_DIR)
        ),
    }

    metrics.stop_timer(started_at)
    save_metrics(metrics, config.output.metrics_report)
    _write_run_report(config, metrics, run_id)
    _save_json(
        STATE_FILE,
        {
            "run_id": run_id,
            "last_run_at": datetime.now(timezone.utc).isoformat(),
            "config_hash": config_hash,
            "source_hashes": current_hashes,
            "all_sources_unchanged": True,
        },
    )

    logger.info("Final dataset created: %s", config.output.final_dataset)
    logger.info("Rejected records written: %s", config.output.rejected_records)
    logger.info("Pipeline completed successfully | run_id=%s", run_id)
    return metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the student multi-source Data Engineering pipeline."
    )
    parser.add_argument(
        "--mode",
        choices=["full", "incremental"],
        default=None,
        help="Processing mode. Defaults to config.json setting.",
    )
    parser.add_argument(
        "--api-url",
        default=None,
        help="Override the online REST API URL for this run.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config()
    if args.api_url:
        config = replace(config, sources=replace(config.sources, api_url=args.api_url))

    metrics = run_pipeline(config, mode=args.mode)

    print("\n" + "=" * 68)
    print("STUDENT MULTI-SOURCE DATA PIPELINE")
    print("=" * 68)
    print(f"Processing mode         : {metrics.processing_mode}")
    print(f"CSV records             : {metrics.source_records.get('CSV', 0)}")
    print(f"API records             : {metrics.source_records.get('API', 0)}")
    print(f"Database records        : {metrics.source_records.get('DATABASE', 0)}")
    print(f"Integrated records      : {metrics.integrated_records}")
    print(f"Valid final records     : {metrics.valid_records}")
    print(f"Rejected records        : {metrics.rejected_records}")
    print(f"Duplicate records       : {metrics.duplicate_records}")
    print(f"Missing values handled  : {metrics.missing_values_handled}")
    print(f"Cross-source mismatches : {metrics.cross_source_mismatches}")
    print(f"Cache hits              : {metrics.cache_hits}")
    print(f"Cache misses            : {metrics.cache_misses}")
    print(f"Processing time (sec)   : {metrics.duration_seconds}")
    print("-" * 68)
    for name, path in metrics.outputs.items():
        print(f"{name:<24}: {path}")
    print("=" * 68)


if __name__ == "__main__":
    main()
