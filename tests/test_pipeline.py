import json
import sqlite3
from dataclasses import replace

import pandas as pd

import app.pipeline as pipeline
from app.config import load_config


class FakeLogger:
    def info(self, *args, **kwargs) -> None:
        pass

    def exception(self, *args, **kwargs) -> None:
        pass


def test_full_pipeline_end_to_end(tmp_path, monkeypatch) -> None:
    # ------------------------------------------------------------------
    # 1. Create isolated test CSV source
    # ------------------------------------------------------------------
    csv_path = tmp_path / "students.csv"
    csv_path.write_text(
        """student_id,student_name,age,major,city
1,Ahmed Ali,21,Computer Science,sanaa
2,Sara Mohammed,22,Artificial Intelligence,aden
""",
        encoding="utf-8",
    )

    # ------------------------------------------------------------------
    # 2. Create isolated test SQLite database
    # ------------------------------------------------------------------
    database_path = tmp_path / "students.db"

    with sqlite3.connect(database_path) as connection:
        connection.executescript(
            """
            CREATE TABLE courses (
                course_id INTEGER PRIMARY KEY,
                course_name TEXT NOT NULL,
                credit_hours INTEGER NOT NULL
            );

            CREATE TABLE enrollments (
                student_id INTEGER NOT NULL,
                course_id INTEGER NOT NULL,
                semester TEXT NOT NULL,
                score REAL NOT NULL
            );
            """
        )

        connection.executemany(
            """
            INSERT INTO courses(course_id, course_name, credit_hours)
            VALUES (?, ?, ?)
            """,
            [
                (101, "Data Engineering", 3),
                (102, "Machine Learning", 3),
            ],
        )

        connection.executemany(
            """
            INSERT INTO enrollments(student_id, course_id, semester, score)
            VALUES (?, ?, ?, ?)
            """,
            [
                (1, 101, "2026-Spring", 91),
                (2, 102, "2026-Spring", 84),
            ],
        )

    # ------------------------------------------------------------------
    # 3. Fake REST API response
    # ------------------------------------------------------------------
    # Student 2 has missing GPA to verify missing-value handling.
    api_dataframe = pd.DataFrame(
        [
            {
                "student_id": 1,
                "gpa": 3.7,
                "attendance": 94,
                "status": "active",
            },
            {
                "student_id": 2,
                "gpa": None,
                "attendance": 88,
                "status": "active",
            },
        ]
    )

    monkeypatch.setattr(
        pipeline,
        "extract_api",
        lambda *args, **kwargs: (
            api_dataframe.copy(),
            "e2e-api-hash",
        ),
    )

    # ------------------------------------------------------------------
    # 4. Isolate pipeline environment
    # ------------------------------------------------------------------
    # The pipeline stores output paths relative to BASE_DIR.
    # tmp_path is used as an isolated temporary project root.
    monkeypatch.setattr(
        pipeline,
        "BASE_DIR",
        tmp_path,
    )

    monkeypatch.setattr(
        pipeline,
        "STATE_FILE",
        tmp_path / "state" / "source_manifest.json",
    )

    monkeypatch.setattr(
        pipeline,
        "CACHE_DIR",
        tmp_path / "state" / "cache",
    )

    monkeypatch.setattr(
        pipeline,
        "configure_logging",
        lambda path: FakeLogger(),
    )

    # ------------------------------------------------------------------
    # 5. Build isolated test configuration
    # ------------------------------------------------------------------
    base_config = load_config()

    output_config = replace(
        base_config.output,
        final_dataset=(
            tmp_path
            / "processed"
            / "final_dataset.csv"
        ),
        student_ml_dataset=(
            tmp_path
            / "processed"
            / "student_ml_dataset.csv"
        ),
        rejected_records=(
            tmp_path
            / "rejected"
            / "rejected_records.csv"
        ),
        metrics_report=(
            tmp_path
            / "reports"
            / "pipeline_metrics.json"
        ),
        run_report=(
            tmp_path
            / "reports"
            / "pipeline_run.md"
        ),
        log_file=(
            tmp_path
            / "logs"
            / "pipeline.log"
        ),
        api_raw_snapshot=(
            tmp_path
            / "raw"
            / "students_api_raw.json"
        ),
        database_raw_snapshot=(
            tmp_path
            / "raw"
            / "enrollments_raw.csv"
        ),
    )

    test_config = replace(
        base_config,
        sources=replace(
            base_config.sources,
            csv_path=csv_path,
            api_url="https://example.test/students",
            database_path=database_path,
        ),
        output=output_config,
    )

    # ------------------------------------------------------------------
    # 6. Run the complete pipeline
    # ------------------------------------------------------------------
    metrics = pipeline.run_pipeline(
        test_config,
        mode="full",
    )

    # ------------------------------------------------------------------
    # 7. Validate pipeline execution metrics
    # ------------------------------------------------------------------
    assert metrics.processing_mode == "full"

    assert metrics.source_records["CSV"] == 2
    assert metrics.source_records["API"] == 2
    assert metrics.source_records["DATABASE"] == 2

    assert metrics.integrated_records == 2
    assert metrics.valid_records == 2
    assert metrics.rejected_records == 0
    assert metrics.missing_values_handled == 1

    # ------------------------------------------------------------------
    # 8. Validate final dataset
    # ------------------------------------------------------------------
    final_dataset = pd.read_csv(
        output_config.final_dataset,
    )

    assert len(final_dataset) == 2

    assert {
        "student_id",
        "performance_level",
        "attendance_status",
        "score_band",
        "source",
    }.issubset(final_dataset.columns)

    assert final_dataset["student_id"].tolist() == [1, 2]

    assert final_dataset["source"].eq(
        "CSV+API+DATABASE"
    ).all()

    # ------------------------------------------------------------------
    # 9. Validate ML dataset
    # ------------------------------------------------------------------
    ml_dataset = pd.read_csv(
        output_config.student_ml_dataset,
    )

    assert len(ml_dataset) == 2
    assert "course_count" in ml_dataset.columns
    assert "average_score" in ml_dataset.columns

    # ------------------------------------------------------------------
    # 10. Validate rejected records
    # ------------------------------------------------------------------
    rejected_dataset = pd.read_csv(
        output_config.rejected_records,
    )

    assert rejected_dataset.empty

    # ------------------------------------------------------------------
    # 11. Validate reports
    # ------------------------------------------------------------------
    assert output_config.metrics_report.exists()
    assert output_config.run_report.exists()

    saved_metrics = json.loads(
        output_config.metrics_report.read_text(
            encoding="utf-8"
        )
    )

    assert saved_metrics["valid_records"] == 2
    assert saved_metrics["integrated_records"] == 2

    # ------------------------------------------------------------------
    # 12. Validate raw API snapshot
    # ------------------------------------------------------------------
    api_snapshot = json.loads(
        output_config.api_raw_snapshot.read_text(
            encoding="utf-8"
        )
    )

    assert len(api_snapshot) == 2

    # Missing GPA must be serialized as JSON null.
    assert api_snapshot[1]["gpa"] is None

    # ------------------------------------------------------------------
    # 13. Validate raw SQLite snapshot
    # ------------------------------------------------------------------
    assert output_config.database_raw_snapshot.exists()
