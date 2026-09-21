from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "students_api.json"

app = FastAPI(
    title="Student Academic Profile API",
    description=(
        "Online REST source for the Student Multi-Source Data Engineering Pipeline. "
        "It exposes academic profile data keyed by student_id."
    ),
    version="1.0.0",
)


def load_students() -> list[dict]:
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


@app.get("/", tags=["System"])
def root() -> dict:
    return {
        "name": "Student Academic Profile API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": ["/health", "/students", "/students/{student_id}"],
    }


@app.get("/health", tags=["System"])
def health() -> dict:
    return {"status": "ok", "service": "student-academic-profile-api"}


@app.get("/students", tags=["Students"])
def get_students(
    status: str | None = Query(default=None),
) -> list[dict]:
    students = load_students()
    if status is None:
        return students
    normalized = status.strip().title()
    return [student for student in students if student["status"].strip().title() == normalized]


@app.get("/students/{student_id}", tags=["Students"])
def get_student(student_id: int) -> dict:
    for student in load_students():
        if student["student_id"] == student_id:
            return student
    raise HTTPException(
        status_code=404,
        detail=f"Student {student_id} not found.",
    )


@app.get("/meta", tags=["System"])
def metadata() -> dict:
    students = load_students()
    return {
        "service": "student-academic-profile-api",
        "environment": os.getenv("ENVIRONMENT", "production"),
        "record_count": len(students),
        "schema": ["student_id", "gpa", "attendance", "status"],
    }
