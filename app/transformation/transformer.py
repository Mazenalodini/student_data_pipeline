from __future__ import annotations

import pandas as pd


def add_derived_columns(
    dataframe: pd.DataFrame,
    minimum_good_attendance: float = 75,
) -> pd.DataFrame:
    df = dataframe.copy()

    def performance_level(gpa: float) -> str:
        if gpa >= 3.5:
            return "Excellent"
        if gpa >= 3.0:
            return "Very Good"
        if gpa >= 2.5:
            return "Good"
        if gpa >= 2.0:
            return "Acceptable"
        return "At Risk"

    df["performance_level"] = df["gpa"].apply(performance_level)
    df["attendance_status"] = df["attendance"].apply(
        lambda value: "Good" if value >= minimum_good_attendance else "Low"
    )
    df["score_band"] = pd.cut(
        df["score"],
        bins=[-0.01, 59.99, 69.99, 79.99, 89.99, 100],
        labels=["F", "D", "C", "B", "A"],
    ).astype("string")
    df["source"] = "CSV+API+DATABASE"
    return df


def build_student_ml_dataset(final_dataset: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        final_dataset.groupby(
            [
                "student_id",
                "student_name",
                "age",
                "major",
                "city",
                "gpa",
                "attendance",
                "status",
                "performance_level",
                "attendance_status",
            ],
            as_index=False,
        )
        .agg(
            course_count=("course_id", "nunique"),
            total_credit_hours=("credit_hours", "sum"),
            average_score=("score", "mean"),
            highest_score=("score", "max"),
            lowest_score=("score", "min"),
        )
    )
    grouped["average_score"] = grouped["average_score"].round(2)
    grouped["highest_score"] = grouped["highest_score"].round(2)
    grouped["lowest_score"] = grouped["lowest_score"].round(2)
    grouped["source"] = "CSV+API+DATABASE"
    return grouped
