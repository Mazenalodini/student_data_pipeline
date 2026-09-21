import sqlite3
from pathlib import Path

from app.sources.database_source import extract_enrollments, validate_enrollments


def test_sqlite_extraction_and_validation(tmp_path: Path) -> None:
    db = tmp_path / "students.db"
    with sqlite3.connect(db) as connection:
        connection.executescript(
            """
            CREATE TABLE courses (
                course_id INTEGER PRIMARY KEY,
                course_name TEXT NOT NULL,
                credit_hours INTEGER NOT NULL
            );
            CREATE TABLE enrollments (
                enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                course_id INTEGER NOT NULL,
                semester TEXT NOT NULL,
                score REAL
            );
            INSERT INTO courses VALUES (1, 'Python Programming', 3);
            INSERT INTO enrollments (student_id, course_id, semester, score)
            VALUES (1001, 1, 'Fall 2026', 95);
            """
        )

    dataframe = extract_enrollments(db)
    valid, rejected, _ = validate_enrollments(dataframe)

    assert len(valid) == 1
    assert rejected == []
    assert valid.iloc[0]["course_name"] == "Python Programming"
