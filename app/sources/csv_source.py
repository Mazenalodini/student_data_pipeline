from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from app.models import RejectedRecord
from app.transformation.cleaner import impute_numeric_median, normalize_text_columns

EXPECTED_COLUMNS = [
    "student_id",
    "student_name",
    "age",
    "major",
    "city",
]

_COLUMN_ALIASES = {
    "student id": "student_id",
    "student_id": "student_id",
    "studentname": "student_name",
    "student name": "student_name",
    "student_name": "student_name",
    "age": "age",
    "major": "major",
    "city": "city",
}


def _normalize_column_name(value: str) -> str:
    key = value.strip().lower().replace("-", " ").replace("_", " ")
    return _COLUMN_ALIASES.get(key, key.replace(" ", "_"))


def extract_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"CSV source not found: {path}")

    dataframe = pd.read_csv(path, dtype="object")
    dataframe.columns = [
        _normalize_column_name(column)
        for column in dataframe.columns
    ]

    missing_columns = set(EXPECTED_COLUMNS) - set(dataframe.columns)
    if missing_columns:
        raise ValueError(
            f"CSV source is missing required columns: {sorted(missing_columns)}"
        )

    return dataframe[EXPECTED_COLUMNS].copy()


def clean_and_validate_csv(
    dataframe: pd.DataFrame,
) -> tuple[pd.DataFrame, list[RejectedRecord], dict[str, int]]:
    df = dataframe.copy()
    rejected: list[RejectedRecord] = []
    stats = {
        "exact_duplicates": 0,
        "duplicate_student_ids": 0,
        "missing_values_handled": 0,
    }

    df["student_id"] = pd.to_numeric(df["student_id"], errors="coerce")
    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    for column in ["student_name", "major", "city"]:
        df[column] = df[column].astype("string")

    # Normalize text before duplicate detection so case/spacing variants can be compared.
    df = normalize_text_columns(df)

    duplicate_mask = df.duplicated(keep="first")
    for _, row in df.loc[duplicate_mask].iterrows():
        rejected.append(
            RejectedRecord(
                source="CSV",
                record_type="student",
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
                source="CSV",
                record_type="student",
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
                    source="CSV",
                    record_type="student",
                    student_id=None,
                    error_reason="Missing student_id",
                    raw_record=_row_to_dict(row),
                )
            )
            drop_indices.append(index)
            continue

        if pd.notna(row["age"]) and not 16 <= float(row["age"]) <= 80:
            rejected.append(
                RejectedRecord(
                    source="CSV",
                    record_type="student",
                    student_id=int(student_id),
                    error_reason="Invalid Age",
                    raw_record=_row_to_dict(row),
                )
            )
            drop_indices.append(index)

    if drop_indices:
        df.drop(index=drop_indices, inplace=True)

    empty_name_mask = df["student_name"].isna() | df["student_name"].eq("")
    for _, row in df.loc[empty_name_mask].iterrows():
        rejected.append(
            RejectedRecord(
                source="CSV",
                record_type="student",
                student_id=_safe_id(row.get("student_id")),
                error_reason="Missing student_name",
                raw_record=_row_to_dict(row),
            )
        )
    df = df.loc[~empty_name_mask].copy()

    df, handled = impute_numeric_median(df, ["age"])
    stats["missing_values_handled"] += handled

    df["student_id"] = df["student_id"].astype(int)
    df["age"] = df["age"].astype(int)

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
