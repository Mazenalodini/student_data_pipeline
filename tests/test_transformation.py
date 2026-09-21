import pandas as pd

from app.transformation.transformer import add_derived_columns, build_student_ml_dataset


def test_derived_columns() -> None:
    dataframe = pd.DataFrame(
        [
            {
                "student_id": 1,
                "student_name": "Student One",
                "age": 22,
                "major": "CS",
                "city": "Sanaa",
                "gpa": 3.8,
                "attendance": 90,
                "status": "Active",
                "course_id": 1,
                "course_name": "Python",
                "credit_hours": 3,
                "semester": "Fall 2026",
                "score": 92,
            }
        ]
    )
    transformed = add_derived_columns(dataframe)
    assert transformed.loc[0, "performance_level"] == "Excellent"
    assert transformed.loc[0, "attendance_status"] == "Good"
    assert transformed.loc[0, "score_band"] == "A"


def test_student_ml_dataset_aggregates_courses() -> None:
    dataframe = pd.DataFrame(
        [
            {
                "student_id": 1,
                "student_name": "Student One",
                "age": 22,
                "major": "CS",
                "city": "Sanaa",
                "gpa": 3.8,
                "attendance": 90,
                "status": "Active",
                "course_id": 1,
                "course_name": "Python",
                "credit_hours": 3,
                "semester": "Fall 2026",
                "score": 90,
                "performance_level": "Excellent",
                "attendance_status": "Good",
                "score_band": "A",
                "source": "CSV+API+DATABASE",
            },
            {
                "student_id": 1,
                "student_name": "Student One",
                "age": 22,
                "major": "CS",
                "city": "Sanaa",
                "gpa": 3.8,
                "attendance": 90,
                "status": "Active",
                "course_id": 2,
                "course_name": "Databases",
                "credit_hours": 3,
                "semester": "Fall 2026",
                "score": 80,
                "performance_level": "Excellent",
                "attendance_status": "Good",
                "score_band": "B",
                "source": "CSV+API+DATABASE",
            },
        ]
    )
    output = build_student_ml_dataset(dataframe)
    assert len(output) == 1
    assert output.loc[0, "course_count"] == 2
    assert output.loc[0, "total_credit_hours"] == 6
