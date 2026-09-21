from __future__ import annotations

import pandas as pd


def normalize_text_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Normalize whitespace and human-readable text casing across a dataset."""
    df = dataframe.copy()
    for column in [
        "student_name",
        "major",
        "city",
        "status",
        "course_name",
        "semester",
    ]:
        if column in df.columns:
            df[column] = df[column].astype("string").str.strip()

    if "city" in df.columns:
        df["city"] = df["city"].str.title()
    if "status" in df.columns:
        df["status"] = df["status"].str.title()
    return df


def impute_numeric_median(
    dataframe: pd.DataFrame,
    columns: list[str],
) -> tuple[pd.DataFrame, int]:
    """Fill missing numeric values with each column's median."""
    df = dataframe.copy()
    handled = 0

    for column in columns:
        if column not in df.columns or not df[column].isna().any():
            continue
        median = df[column].median()
        missing = int(df[column].isna().sum())
        df[column] = df[column].fillna(median)
        handled += missing

    return df, handled
