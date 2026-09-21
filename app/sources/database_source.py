from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd

from app.models import RejectedRecord
from app.transformation.cleaner import impute_numeric_median, normalize_text_columns


EXPECTED_COLUMNS = [
    "student_id",
    "course_id",
    "course_name",
    "credit_hours",
    "semester",
    "score",
]


def get_connection(database_path: Path) -> sqlite3.Connection:
    if not database_path.exists():
        raise FileNotFoundError(
            f"SQLite database not found: {database_path}. "
            "Run scripts/setup_database.py first."
        )

    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection


def extract_enrollments(database_path: Path) -> pd.DataFrame:
    query = """
        SELECT
            e.student_id,
            e.course_id,
            c.course_name,
            c.credit_hours,
            e.semester,
            e.score
        FROM enrollments AS e
        INNER JOIN courses AS c
            ON c.course_id = e.course_id
        ORDER BY e.student_id, e.course_id, e.semester;
    """

    with get_connection(database_path) as connection:
        return pd.read_sql_query(query, connection)


def validate_enrollments(
    dataframe: pd.DataFrame,
) -> tuple[pd.DataFrame, list[RejectedRecord], dict[str, int]]:
    df = dataframe.copy()
    rejected: list[RejectedRecord] = []
    stats = {
        "exact_duplicates": 0,
        "duplicate_enrollments": 0,
        "missing_values_handled": 0,
    }

    for column in ["student_id", "course_id", "credit_hours", "score"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    df = normalize_text_columns(df)

    duplicate_mask = df.duplicated(keep="first")
    for _, row in df.loc[duplicate_mask].iterrows():
        rejected.append(
            RejectedRecord(
                source="DATABASE",
                record_type="enrollment",
                student_id=_safe_id(row.get("student_id")),
                error_reason="Duplicate enrollment record",
                raw_record=_row_to_dict(row),
            )
        )
    stats["exact_duplicates"] = int(duplicate_mask.sum())
    df = df.loc[~duplicate_mask].copy()

    duplicate_business_key_mask = df.duplicated(
        subset=["student_id", "course_id", "semester"],
        keep="first",
    )
    for _, row in df.loc[duplicate_business_key_mask].iterrows():
        rejected.append(
            RejectedRecord(
                source="DATABASE",
                record_type="enrollment",
                student_id=_safe_id(row.get("student_id")),
                error_reason="Duplicate student-course-semester",
                raw_record=_row_to_dict(row),
            )
        )
    stats["duplicate_enrollments"] = int(duplicate_business_key_mask.sum())
    df = df.loc[~duplicate_business_key_mask].copy()

    drop_indices: list[Any] = []
    for index, row in df.iterrows():
        student_id = row["student_id"]
        if pd.isna(student_id):
            rejected.append(
                RejectedRecord(
                    source="DATABASE",
                    record_type="enrollment",
                    student_id=None,
                    error_reason="Missing student_id",
                    raw_record=_row_to_dict(row),
                )
            )
            drop_indices.append(index)
            continue

        if pd.isna(row["course_id"]):
            rejected.append(
                RejectedRecord(
                    source="DATABASE",
                    record_type="enrollment",
                    student_id=int(student_id),
                    error_reason="Missing course_id",
                    raw_record=_row_to_dict(row),
                )
            )
            drop_indices.append(index)
            continue

        if pd.isna(row["score"]):
            continue

        if not 0 <= float(row["score"]) <= 100:
            rejected.append(
                RejectedRecord(
                    source="DATABASE",
                    record_type="enrollment",
                    student_id=int(student_id),
                    error_reason="Invalid Score",
                    raw_record=_row_to_dict(row),
                )
            )
            drop_indices.append(index)

    if drop_indices:
        df.drop(index=drop_indices, inplace=True)

    df, handled = impute_numeric_median(df, ["score"])
    stats["missing_values_handled"] += handled

    df["student_id"] = df["student_id"].astype(int)
    df["course_id"] = df["course_id"].astype(int)
    df["credit_hours"] = df["credit_hours"].astype(int)

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
