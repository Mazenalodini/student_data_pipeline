from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pandas as pd


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    errors: list[str]


def validate_unique_student_ids(dataframe: pd.DataFrame) -> ValidationResult:
    errors: list[str] = []
    if dataframe["student_id"].isna().any():
        errors.append("student_id cannot be NULL")
    if dataframe["student_id"].duplicated().any():
        errors.append("student_id must be unique")
    return ValidationResult(valid=not errors, errors=errors)


def validate_range(
    dataframe: pd.DataFrame,
    column: str,
    minimum: float,
    maximum: float,
) -> ValidationResult:
    errors = []
    values = pd.to_numeric(dataframe[column], errors="coerce")
    if values.isna().any():
        errors.append(f"{column} contains non-numeric or missing values")
    if not values.dropna().between(minimum, maximum).all():
        errors.append(f"{column} must be between {minimum} and {maximum}")
    return ValidationResult(valid=not errors, errors=errors)


def validate_required_text(dataframe: pd.DataFrame, column: str) -> ValidationResult:
    values = dataframe[column].astype("string").str.strip()
    errors = []
    if values.isna().any() or values.eq("").any():
        errors.append(f"{column} cannot be NULL or empty")
    return ValidationResult(valid=not errors, errors=errors)


def validate_final_dataset(dataframe: pd.DataFrame) -> ValidationResult:
    required = {
        "student_id",
        "student_name",
        "age",
        "major",
        "city",
        "gpa",
        "attendance",
        "status",
        "course_id",
        "course_name",
        "credit_hours",
        "semester",
        "score",
        "performance_level",
        "attendance_status",
        "source",
    }
    missing = required - set(dataframe.columns)
    errors = []
    if missing:
        errors.append(f"Missing final columns: {sorted(missing)}")
        return ValidationResult(valid=False, errors=errors)

    checks: Iterable[ValidationResult] = (
        validate_range(dataframe, "age", 16, 80),
        validate_range(dataframe, "gpa", 0, 4),
        validate_range(dataframe, "attendance", 0, 100),
        validate_range(dataframe, "score", 0, 100),
        validate_required_text(dataframe, "student_name"),
        validate_required_text(dataframe, "course_name"),
    )

    for result in checks:
        errors.extend(result.errors)

    if dataframe.empty:
        errors.append("Final dataset must not be empty")

    return ValidationResult(valid=not errors, errors=errors)
