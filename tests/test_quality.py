import pandas as pd

from app.validation.quality import validate_final_dataset


def test_final_dataset_validation_passes_for_valid_data() -> None:
    dataframe = pd.DataFrame(
        [
            {
                "student_id": 1,
                "student_name": "Student",
                "age": 22,
                "major": "CS",
                "city": "Sanaa",
                "gpa": 3.5,
                "attendance": 90,
                "status": "Active",
                "course_id": 1,
                "course_name": "Python",
                "credit_hours": 3,
                "semester": "Fall 2026",
                "score": 95,
                "performance_level": "Excellent",
                "attendance_status": "Good",
                "source": "CSV+API+DATABASE",
            }
        ]
    )
    result = validate_final_dataset(dataframe)
    assert result.valid
