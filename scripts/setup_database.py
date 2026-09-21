from __future__ import annotations

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATABASE_PATH = BASE_DIR / "database" / "students.db"

COURSES = [
    (1, "Python Programming", 3),
    (2, "Relational Databases", 3),
    (3, "Data Engineering Fundamentals", 3),
    (4, "Machine Learning", 4),
    (5, "Artificial Intelligence", 4),
]

ENROLLMENTS = [
    (1001, 1, "Fall 2026", 91),
    (1001, 2, "Fall 2026", 88),
    (1001, 3, "Fall 2026", 94),
    (1002, 1, "Fall 2026", 97),
    (1002, 4, "Fall 2026", 93),
    (1003, 2, "Fall 2026", 82),
    (1003, 3, "Fall 2026", 86),
    (1004, 1, "Fall 2026", 89),
    (1004, 5, "Fall 2026", 91),
    (1005, 2, "Fall 2026", None),
    (1005, 3, "Fall 2026", 78),
    (1006, 1, "Fall 2026", 74),
    (1006, 4, "Fall 2026", 69),
    (1010, 3, "Fall 2026", 87),
    (1010, 2, "Fall 2026", 84),
    (1011, 4, "Fall 2026", 99),
    (1012, 3, "Fall 2026", 81),
    (1012, 5, "Fall 2026", 85),
    (1012, 5, "Fall 2026", 85),
    (1098, 1, "Fall 2026", 90),
    (1004, 4, "Fall 2026", 103),
]


def setup_database() -> None:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(
            """
            DROP TABLE IF EXISTS enrollments;
            DROP TABLE IF EXISTS courses;

            CREATE TABLE courses (
                course_id INTEGER PRIMARY KEY,
                course_name TEXT NOT NULL UNIQUE,
                credit_hours INTEGER NOT NULL CHECK (credit_hours BETWEEN 1 AND 6)
            );

            CREATE TABLE enrollments (
                enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                course_id INTEGER NOT NULL,
                semester TEXT NOT NULL,
                score REAL,
                FOREIGN KEY (course_id) REFERENCES courses(course_id)
            );

            CREATE INDEX idx_enrollments_student_id
                ON enrollments(student_id);
            CREATE INDEX idx_enrollments_course_id
                ON enrollments(course_id);
            """
        )
        connection.executemany(
            "INSERT INTO courses (course_id, course_name, credit_hours) VALUES (?, ?, ?)",
            COURSES,
        )
        connection.executemany(
            """
            INSERT INTO enrollments (student_id, course_id, semester, score)
            VALUES (?, ?, ?, ?)
            """,
            ENROLLMENTS,
        )
        connection.commit()

    print(f"SQLite database created: {DATABASE_PATH}")


if __name__ == "__main__":
    setup_database()
