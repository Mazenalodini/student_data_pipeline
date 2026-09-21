import pandas as pd

from app.transformation.integration import integrate_sources


def test_sources_integrate_by_student_id() -> None:
    students = pd.DataFrame(
        [
            {
                "student_id": 1001,
                "student_name": "Ahmed",
                "age": 22,
                "major": "CS",
                "city": "Sanaa",
            }
        ]
    )
    api = pd.DataFrame(
        [{"student_id": 1001, "gpa": 3.5, "attendance": 90, "status": "Active"}]
    )
    db = pd.DataFrame(
        [
            {
                "student_id": 1001,
                "course_id": 1,
                "course_name": "Python",
                "credit_hours": 3,
                "semester": "Fall 2026",
                "score": 95,
            }
        ]
    )

    integrated, rejected = integrate_sources(students, api, db)

    assert len(integrated) == 1
    assert integrated.loc[0, "gpa"] == 3.5
    assert integrated.loc[0, "course_name"] == "Python"
    assert rejected == []
