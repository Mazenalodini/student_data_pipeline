from __future__ import annotations

import json
import time
from typing import Any

import pandas as pd
import requests

from app.models import RejectedRecord
from app.transformation.cleaner import impute_numeric_median, normalize_text_columns
from app.utils.hashing import sha256_text

EXPECTED_COLUMNS = ["student_id", "gpa", "attendance", "status"]


class APIExtractionError(RuntimeError):
    """Raised when the online REST source cannot be safely extracted."""


def extract_api(
    url: str,
    timeout: int = 15,
    max_retries: int = 3,
    backoff_seconds: float = 1.0,
) -> tuple[pd.DataFrame, str]:
    if not url or "YOUR-DEPLOYED-API" in url:
        raise APIExtractionError(
            "Online API URL is not configured. Set STUDENT_PIPELINE_API_URL or update config.json."
        )

    headers = {
        "Accept": "application/json",
        "User-Agent": "student-data-pipeline/1.0",
    }

    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=timeout,
            )
            response.raise_for_status()
            break
        except requests.Timeout as exc:
            last_error = exc
            if attempt == max_retries:
                raise APIExtractionError(
                    f"REST API timeout after {max_retries} attempts."
                ) from exc
            time.sleep(backoff_seconds * attempt)
        except requests.ConnectionError as exc:
            last_error = exc
            if attempt == max_retries:
                raise APIExtractionError(
                    f"REST API connection failed after {max_retries} attempts."
                ) from exc
            time.sleep(backoff_seconds * attempt)
        except requests.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else "unknown"
            raise APIExtractionError(
                f"REST API returned HTTP {status_code}."
            ) from exc
        except requests.RequestException as exc:
            raise APIExtractionError(f"REST API request failed: {exc}") from exc
    else:
        raise APIExtractionError(f"REST API request failed: {last_error}")

    try:
        payload = response.json()
    except ValueError as exc:
        raise APIExtractionError("REST API returned invalid JSON.") from exc

    if not isinstance(payload, list) or not payload:
        raise APIExtractionError(
            "REST API response must be a non-empty JSON array."
        )

    dataframe = pd.DataFrame(payload)
    missing_columns = set(EXPECTED_COLUMNS) - set(dataframe.columns)
    if missing_columns:
        raise APIExtractionError(
            "REST API response is missing required columns: "
            + ", ".join(sorted(missing_columns))
        )

    canonical_payload = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    payload_hash = sha256_text(canonical_payload)
    return dataframe[EXPECTED_COLUMNS].copy(), payload_hash


def clean_and_validate_api(
    dataframe: pd.DataFrame,
) -> tuple[pd.DataFrame, list[RejectedRecord], dict[str, int]]:
    df = dataframe.copy()
    rejected: list[RejectedRecord] = []
    stats = {
        "exact_duplicates": 0,
        "duplicate_student_ids": 0,
        "missing_values_handled": 0,
    }

    for column in ["student_id", "gpa", "attendance"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    df = normalize_text_columns(df)

    duplicate_mask = df.duplicated(keep="first")
    for _, row in df.loc[duplicate_mask].iterrows():
        rejected.append(
            RejectedRecord(
                source="API",
                record_type="academic_profile",
                student_id=_safe_id(row.get("student_id")),
                error_reason="Duplicate record",
                raw_record=_row_to_dict(row),
            )
        )
    stats["exact_duplicates"] = int(duplicate_mask.sum())
    df = df.loc[~duplicate_mask].copy()

    duplicate_id_mask = df.duplicated(subset=["student_id"], keep="first")
    for _, row in df.loc[duplicate_id_mask].iterrows():
        rejected.append(
            RejectedRecord(
                source="API",
                record_type="academic_profile",
                student_id=_safe_id(row.get("student_id")),
                error_reason="Duplicate student_id",
                raw_record=_row_to_dict(row),
            )
        )
    stats["duplicate_student_ids"] = int(duplicate_id_mask.sum())
    df = df.loc[~duplicate_id_mask].copy()

    drop_indices: list[Any] = []
    for index, row in df.iterrows():
        student_id = row["student_id"]
        if pd.isna(student_id):
            rejected.append(
                RejectedRecord(
                    source="API",
                    record_type="academic_profile",
                    student_id=None,
                    error_reason="Missing student_id",
                    raw_record=_row_to_dict(row),
                )
            )
            drop_indices.append(index)
            continue

        if pd.notna(row["gpa"]) and not 0 <= float(row["gpa"]) <= 4:
            rejected.append(
                RejectedRecord(
                    source="API",
                    record_type="academic_profile",
                    student_id=int(student_id),
                    error_reason="Invalid GPA",
                    raw_record=_row_to_dict(row),
                )
            )
            drop_indices.append(index)
            continue

        if pd.notna(row["attendance"]) and not 0 <= float(row["attendance"]) <= 100:
            rejected.append(
                RejectedRecord(
                    source="API",
                    record_type="academic_profile",
                    student_id=int(student_id),
                    error_reason="Invalid Attendance",
                    raw_record=_row_to_dict(row),
                )
            )
            drop_indices.append(index)

    if drop_indices:
        df.drop(index=drop_indices, inplace=True)

    df, handled = impute_numeric_median(df, ["gpa", "attendance"])
    stats["missing_values_handled"] += handled

    df["student_id"] = df["student_id"].astype(int)
    return df.reset_index(drop=True), rejected, stats


def _safe_id(value: Any) -> Any:
    if pd.isna(value):
        return None
    return int(value)


def _row_to_dict(row: pd.Series) -> dict[str, Any]:
    return {
        key: (None if pd.isna(value) else value)
        for key, value in row.to_dict().items()
    }
