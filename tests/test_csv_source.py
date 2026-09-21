from pathlib import Path

from app.sources.csv_source import clean_and_validate_csv, extract_csv


BASE_DIR = Path(__file__).resolve().parents[1]


def test_csv_loads_and_normalizes_columns() -> None:
    dataframe = extract_csv(BASE_DIR / "data/raw/students.csv")
    assert set(dataframe.columns) == {
        "student_id",
        "student_name",
        "age",
        "major",
        "city",
    }
    assert len(dataframe) == 14


def test_csv_rejects_invalid_and_duplicate_rows() -> None:
    dataframe = extract_csv(BASE_DIR / "data/raw/students.csv")
    valid, rejected, stats = clean_and_validate_csv(dataframe)
    reasons = {record.error_reason for record in rejected}

    assert "Invalid Age" in reasons
    assert "Duplicate record" in reasons
    assert len(valid) < len(dataframe)
    assert stats["exact_duplicates"] >= 1
