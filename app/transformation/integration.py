from __future__ import annotations

import pandas as pd

from app.models import RejectedRecord


def integrate_sources(
    students: pd.DataFrame,
    api_profiles: pd.DataFrame,
    enrollments: pd.DataFrame,
) -> tuple[pd.DataFrame, list[RejectedRecord]]:
    rejected: list[RejectedRecord] = []

    student_ids = set(students["student_id"].astype(int))
    api_ids = set(api_profiles["student_id"].astype(int))

    for _, row in api_profiles[~api_profiles["student_id"].isin(student_ids)].iterrows():
        rejected.append(
            RejectedRecord(
                source="API",
                record_type="academic_profile",
                student_id=int(row["student_id"]),
                error_reason="student_id not found in CSV source",
                raw_record=row.to_dict(),
            )
        )

    db_ids = set(enrollments["student_id"].astype(int))
    for _, row in enrollments[~enrollments["student_id"].isin(student_ids)].iterrows():
        rejected.append(
            RejectedRecord(
                source="DATABASE",
                record_type="enrollment",
                student_id=int(row["student_id"]),
                error_reason="student_id not found in CSV source",
                raw_record=row.to_dict(),
            )
        )

    compatible_api = api_profiles[api_profiles["student_id"].isin(student_ids)].copy()
    compatible_db = enrollments[enrollments["student_id"].isin(student_ids)].copy()

    missing_api = sorted(student_ids - api_ids)
    for student_id in missing_api:
        rejected.append(
            RejectedRecord(
                source="INTEGRATION",
                record_type="student",
                student_id=student_id,
                error_reason="Student missing from REST API source",
                raw_record={"student_id": student_id},
            )
        )

    integrated = students.merge(
        compatible_api,
        on="student_id",
        how="inner",
        validate="one_to_one",
    )
    integrated = integrated.merge(
        compatible_db,
        on="student_id",
        how="inner",
        validate="one_to_many",
    )

    return integrated, rejected
