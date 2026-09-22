import pytest
import requests

import app.sources.api_source as api_source


class FakeResponse:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> list[dict]:
        return [
            {"student_id": 1, "gpa": 3.5, "attendance": 90, "status": "active"},
            {"student_id": 2, "gpa": None, "attendance": 85, "status": "Active"},
        ]


class InvalidJSONResponse(FakeResponse):
    def json(self) -> list[dict]:
        raise ValueError("Invalid JSON")


class EmptyResponse(FakeResponse):
    def json(self) -> list[dict]:
        return []


class MissingColumnsResponse(FakeResponse):
    def json(self) -> list[dict]:
        return [
            {"student_id": 1, "gpa": 3.5, "status": "active"},
        ]


class HTTPErrorResponse(FakeResponse):
    def raise_for_status(self) -> None:
        response = requests.Response()
        response.status_code = 503
        raise requests.HTTPError(
            "Service Unavailable",
            response=response,
        )


def test_api_extraction_handles_json(monkeypatch) -> None:
    monkeypatch.setattr(
        api_source.requests,
        "get",
        lambda *args, **kwargs: FakeResponse(),
    )

    dataframe, payload_hash = api_source.extract_api(
        "https://example.com/students"
    )

    assert len(dataframe) == 2
    assert set(dataframe.columns) == {
        "student_id",
        "gpa",
        "attendance",
        "status",
    }
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


def test_api_extraction_retries_on_connection_error(monkeypatch) -> None:
    calls = {"count": 0}

    def fake_get(*args, **kwargs):
        calls["count"] += 1
        raise requests.ConnectionError("connection failed")

    monkeypatch.setattr(api_source.requests, "get", fake_get)
    monkeypatch.setattr(api_source.time, "sleep", lambda *_: None)

    with pytest.raises(api_source.APIExtractionError, match="connection failed"):
        api_source.extract_api(
            "https://example.com/students",
            max_retries=3,
            backoff_seconds=0,
        )

    assert calls["count"] == 3


def test_api_extraction_retries_on_timeout(monkeypatch) -> None:
    calls = {"count": 0}

    def fake_get(*args, **kwargs):
        calls["count"] += 1
        raise requests.Timeout("request timed out")

    monkeypatch.setattr(api_source.requests, "get", fake_get)
    monkeypatch.setattr(api_source.time, "sleep", lambda *_: None)

    with pytest.raises(api_source.APIExtractionError, match="timeout"):
        api_source.extract_api(
            "https://example.com/students",
            max_retries=3,
            backoff_seconds=0,
        )

    assert calls["count"] == 3


def test_api_extraction_handles_http_error(monkeypatch) -> None:
    monkeypatch.setattr(
        api_source.requests,
        "get",
        lambda *args, **kwargs: HTTPErrorResponse(),
    )

    with pytest.raises(
        api_source.APIExtractionError,
        match="HTTP 503",
    ):
        api_source.extract_api("https://example.com/students")


def test_api_extraction_rejects_invalid_json(monkeypatch) -> None:
    monkeypatch.setattr(
        api_source.requests,
        "get",
        lambda *args, **kwargs: InvalidJSONResponse(),
    )

    with pytest.raises(
        api_source.APIExtractionError,
        match="invalid JSON",
    ):
        api_source.extract_api("https://example.com/students")


def test_api_extraction_rejects_empty_response(monkeypatch) -> None:
    monkeypatch.setattr(
        api_source.requests,
        "get",
        lambda *args, **kwargs: EmptyResponse(),
    )

    with pytest.raises(
        api_source.APIExtractionError,
        match="non-empty JSON array",
    ):
        api_source.extract_api("https://example.com/students")


def test_api_extraction_rejects_missing_columns(monkeypatch) -> None:
    monkeypatch.setattr(
        api_source.requests,
        "get",
        lambda *args, **kwargs: MissingColumnsResponse(),
    )

    with pytest.raises(
        api_source.APIExtractionError,
        match="missing required columns",
    ):
        api_source.extract_api("https://example.com/students")
