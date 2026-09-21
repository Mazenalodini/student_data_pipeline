PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS courses (
    course_id INTEGER PRIMARY KEY,
    course_name TEXT NOT NULL UNIQUE,
    credit_hours INTEGER NOT NULL CHECK (credit_hours BETWEEN 1 AND 6)
);

CREATE TABLE IF NOT EXISTS enrollments (
    enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    semester TEXT NOT NULL,
    score REAL
);

CREATE INDEX IF NOT EXISTS idx_enrollments_student_id
    ON enrollments(student_id);

CREATE INDEX IF NOT EXISTS idx_enrollments_course_id
    ON enrollments(course_id);
