import app.sources.api_source as api_source


class FakeResponse:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> list[dict]:
        return [
            {"student_id": 1, "gpa": 3.5, "attendance": 90, "status": "active"},
            {"student_id": 2, "gpa": None, "attendance": 85, "status": "Active"},
        ]


def test_api_extraction_handles_json(monkeypatch) -> None:
    monkeypatch.setattr(
        api_source.requests,
        "get",
        lambda *args, **kwargs: FakeResponse(),
    )
    dataframe, payload_hash = api_source.extract_api("https://example.com/students")
    assert len(dataframe) == 2
    assert set(dataframe.columns) == {"student_id", "gpa", "attendance", "status"}
    assert len(payload_hash) == 64


def test_api_validation_handles_missing_gpa(monkeypatch) -> None:
    monkeypatch.setattr(
        api_source.requests,
        "get",
        lambda *args, **kwargs: FakeResponse(),
    )
    dataframe, _ = api_source.extract_api("https://example.com/students")
    valid, rejected, stats = api_source.clean_and_validate_api(dataframe)
    assert len(rejected) == 0
    assert valid["gpa"].notna().all()
    assert stats["missing_values_handled"] == 1
